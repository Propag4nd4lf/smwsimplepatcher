#####################################################################
###                                                               ###
### Name: Super Mario World Rom Hack Hub                          ###
### Description: Download & Patch SMW hacks directly.             ###
### By: Propagandalf                                              ###
###                                                               ###
#####################################################################
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5 import uic
from ui_about import Ui_dialogAbout
from ui_main import Ui_MainWindow
import bps.apply
import bps.io
import bs4 as bs
import requests
import re
import platform
import sqlite3
import os
import shutil
import zipfile
import py7zr
import datetime
import time
import random
import sys
import webbrowser
import urllib
import subprocess

version = '1.0.1'

###################
### MAIN WINDOW ###
###################


class MainWindow(QtWidgets.QMainWindow):
    snesRomInfoUrl = 'https://www.smwcentral.net/?p=section&a=details&id='
    githubLink = 'https://github.com/Propag4nd4lf/smwsimplepatcher'
    currentDir = None
    dbFile = '/smwc.db'
    conn = None
    currentOS = None
    tableRowCount = None
    disableDownloadEssentials = 0
    selectedId = None
    gamePics = []
    gamePicsId = None
    buttonStates = []
    sort = {}

    ##################
    ### INITIALIZE ###
    ##################
    def __init__(self):
        global version
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle(
            'SMW: Simple Patcher - v{}'.format(version))

        self.currentDir = self.getCurrentDir()
        icon = QtGui.QIcon(':/img/icon.png')
        self.setWindowIcon(icon)

        # KEYPRESSES
        MainWindow.keyPressEvent = self.onKeyPressEvent

        # INIT TABLE
        self.initTable()

        # DISABLE MORE INFORMATION FRAME AT START
        self.ui.frame_more_info.setMaximumWidth(0)
        self.ui.frame_more_info.setMinimumWidth(0)

        # SET UP THREADS & BUTTONS
        self.ui.btnUpdateDatabase.clicked.connect(self.workerUpdateDatabase)
        self.ui.btnDownloadEssentialsFiles.clicked.connect(
            self.workerDownloadEssentials)
        self.ui.btnMoreInformation.clicked.connect(
            lambda: UIFunctions.toggleMoreInformation(self, 332, True))
        self.ui.btnVisitWebsite.clicked.connect(self.openWebsite)
        self.ui.btnDownloadRom.clicked.connect(self.workerDownloadAndPatchRoms)
        self.ui.btnSidebarDownload.clicked.connect(
            self.workerDownloadAndPatchRom)
        self.ui.btnSetOutputFolder.clicked.connect(self.setOutputFolder)
        self.ui.btnOpenZip.clicked.connect(self.openZipFolder)
        self.ui.btnNextImage.clicked.connect(self.nextImage)
        self.ui.btnPreviousImage.clicked.connect(self.previousImage)
        self.ui.btnUpdateInfo.clicked.connect(self.updateInfo)
        self.ui.btnHelp.clicked.connect(self.helpDialog)
        self.ui.btnOpenRomFolder.clicked.connect(self.openRomFolder)
        self.ui.btnGithub.clicked.connect(self.openGithub)

        # SORT HEADER
        self.ui.tableWidget.horizontalHeader().sectionClicked.connect(self.sortHeader)

        # CONNECT SEARCH
        self.ui.inputSearch.textChanged.connect(self.searchRom)

        # ADD ON CLICK EVENT
        self.ui.tableWidget.clicked.connect(self.onLeftClick)

        # MAKE THE MAIN WINDOW NOT RESIZEABLE
        self.setFixedSize(self.size())

        # GET OS, INITIALIZE DATABASE & CHECK FOR ESSENTIAL FILES
        self.getOS()
        self.checkForEssentialFiles()
        self.initDatabase()

        # OUTPUT ROMS OUTPUTFODLER
        op = self.getSetting('outputFolder')
        print('Output Folder:', op)

    ####################
    ### CUSTOM STUFF ###
    ####################
    def closeEvent(self, event):
        exit = self.messageBox(
            'Are you sure you want to\nclose the program?', 'Close', 'cancel', buttons=True)
        if exit:
            event.accept()  # let the window close
        else:
            event.ignore()

    def onKeyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            exit = self.messageBox(
                'Are you sure you want to\nclose the program?', 'Close', 'cancel', buttons=True)
            if exit == True:
                self.disconnect()
                sys.exit(0)

        # DEBUG
        if e.key() == QtCore.Qt.Key_F1:
            print(self.getCheckedList())

    def createFolder(self, folder):
        # CREATE FOLDER
        try:
            if self.currentOS == 'Windows':
                os.makedirs(self.currentDir+'/data/'+folder, exist_ok=True)
            if self.currentOS == 'MacOS':
                os.makedirs(self.currentDir+'/data/'+folder)
            if self.currentOS == 'Linux':
                os.makedirs(self.currentDir+'/data/'+folder)
            print('Created folder: /data/'+folder)
            return True
        except OSError as err:
            print('Could not create folder: /data/'+folder,
                  'The folder maybe already exist...?')
            return False

    def deleteFolder(self, folder):
        try:
            shutil.rmtree(self.currentDir+'/data/'+folder)
            print('Deleted folder: /data/'+folder)
            return True
        except:
            print('Could not delete folder: /data/'+folder,
                  'The folder maybe already deleted...?')
            return False

    def getOS(self):
        curOS = platform.system()
        if curOS == 'Darwin':
            self.currentOS = 'MacOS'
        elif curOS == 'Linux':
            self.currentOS = 'Linux'
        elif curOS == 'Windows':
            self.currentOS = 'Windows'
        else:
            print('Could not get correct system.')
            return False
        print('Currently on:', self.currentOS)

    def getHtmlPageInfo(self, id):
        url = 'https://www.smwcentral.net/?p=section&a=details&id=' + str(id)
        return url

    def convertFloatToDecimal(self, f=0.0, precision=2):
        return ("%." + str(precision) + "f") % f

    def formatFileSize(self, size, sizeIn, sizeOut, precision=0):
        assert sizeIn.upper() in {"B", "KB", "MB", "GB"}, "sizeIn type error"
        assert sizeOut.upper() in {"B", "KB", "MB", "GB"}, "sizeOut type error"
        if sizeIn == "B":
            if sizeOut == "KB":
                return self.convertFloatToDecimal((size/1024.0), precision)
            elif sizeOut == "MB":
                return self.onvertFloatToDecimal((size/1024.0**2), precision)
            elif sizeOut == "GB":
                return self.convertFloatToDecimal((size/1024.0**3), precision)
        elif sizeIn == "KB":
            if sizeOut == "B":
                return self.convertFloatToDecimal((size*1024.0), precision)
            elif sizeOut == "MB":
                return self.convertFloatToDecimal((size/1024.0), precision)
            elif sizeOut == "GB":
                return self.convertFloatToDecimal((size/1024.0**2), precision)
        elif sizeIn == "MB":
            if sizeOut == "B":
                return self.convertFloatToDecimal((size*1024.0**2), precision)
            elif sizeOut == "KB":
                return self.convertFloatToDecimal((size*1024.0), precision)
            elif sizeOut == "GB":
                return self.convertFloatToDecimal((size/1024.0), precision)
        elif sizeIn == "GB":
            if sizeOut == "B":
                return self.convertFloatToDecimal((size*1024.0**3), precision)
            elif sizeOut == "KB":
                return self.convertFloatToDecimal((size*1024.0**2), precision)
            elif sizeOut == "MB":
                return self.convertFloatToDecimal((size*1024.0), precision)

    def getCurrentDir(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return application_path

    def sortHeader(self, i):
        #print("index clicked is " + str(i))
        if i == 1:
            column = 'date'
        elif i == 2:
            column = 'name'
        elif i == 3:
            column = 'type'
        elif i == 4:
            column = 'length'
        elif i == 5:
            column = 'rating'
        elif i == 6:
            column = 'approved'
        elif i == 7:
            column = 'downloads'
        elif i == 9:
            column = 'demo'
        elif i == 10:
            column = 'featured'
        # elif i == 12:
        #    column = 'size'
        else:
            return

        if self.sort['column'] == column:
            if self.sort['direction'] == 'DESC':
                direction = 'ASC'
            else:
                direction = 'DESC'
        else:
            direction = 'DESC'

        self.sort = {
            'column': column,
            'direction': direction
        }

        self.removeDataFromList()
        data = self.getAllHacks(self.sort['column'], self.sort['direction'])
        self.loadDataToList(data)
        self.ui.inputSearch.setPlainText('')

    ##################
    ### BUTTONS/UI ###
    ##################
    def nextImage(self):
        try:
            amountOfImages = len(self.gamePics)
            if self.gamePicsId < amountOfImages-1:
                self.gamePicsId += 1
                pngImage = QPixmap(self.gamePics[self.gamePicsId])
                self.ui.labelGameImage.setPixmap(pngImage)

                output = '[{}/{}]'.format(self.gamePicsId+1, amountOfImages)
                self.ui.labelImageNumber.setText(output)
            else:
                self.gamePicsId = 0
                pngImage = QPixmap(self.gamePics[self.gamePicsId])
                self.ui.labelGameImage.setPixmap(pngImage)

                output = '[{}/{}]'.format(self.gamePicsId+1, amountOfImages)
                self.ui.labelImageNumber.setText(output)
        except:
            print('Could not show next image...')

    def previousImage(self):
        try:
            amountOfImages = len(self.gamePics)
            if self.gamePicsId > 0:
                self.gamePicsId -= 1
                pngImage = QPixmap(self.gamePics[self.gamePicsId])
                self.ui.labelGameImage.setPixmap(pngImage)

                output = '[{}/{}]'.format(self.gamePicsId+1, amountOfImages)
                self.ui.labelImageNumber.setText(output)
            else:
                self.gamePicsId = amountOfImages-1
                pngImage = QPixmap(self.gamePics[self.gamePicsId])
                self.ui.labelGameImage.setPixmap(pngImage)

                output = '[{}/{}]'.format(self.gamePicsId+1, amountOfImages)
                self.ui.labelImageNumber.setText(output)
        except:
            print('Could not show next image...')

    def openZipFolder(self):
        try:
            index = self.getListIndex()
            if (isinstance(index.row(), int)):
                id = index.sibling(index.row(), 0).data()
                folder = self.currentDir+'\\data\\hacks\\'+id
                subprocess.Popen('explorer "{}"'.format(folder))
        except:
            return

    def setOutputFolder(self):
        # Select output folder
        path = str(QFileDialog.getExistingDirectory(
            self, "Select Output Directory"))
        if path == "":
            print('No folder selected...')
            return False
        else:
            path.replace('\\', '/')
            self.setSetting('outputFolder', path)
            print('Folder changed to:', path)

    def openWebsite(self):
        item = self.getListIndex()
        try:
            if (isinstance(item.row(), int)):
                id = item.sibling(item.row(), 0).data()
                website = self.snesRomInfoUrl + str(id)
                webbrowser.open_new_tab(website)
        except:
            print('No row selected...')

    def searchRom(self):
        try:
            searchFor = self.ui.inputSearch.toPlainText().lower()
            # GET ROW COUNT
            for row in range(self.ui.tableWidget.rowCount()):
                name = self.ui.tableWidget.item(row, 2).text().lower()
                if searchFor in name:
                    self.ui.tableWidget.showRow(row)
                else:
                    self.ui.tableWidget.hideRow(row)
        except:
            pass

    def setButtonsEnabled(self, boolean):
        if boolean == False:
            self.buttonStates = []
            states = [
                {
                    'ui': self.ui.btnMoreInformation,
                    'state': self.ui.btnMoreInformation.isEnabled()
                },
                {
                    'ui': self.ui.btnUpdateDatabase,
                    'state': self.ui.btnUpdateDatabase.isEnabled()
                },
                {
                    'ui': self.ui.btnGithub,
                    'state': self.ui.btnGithub.isEnabled()
                },
                {
                    'ui': self.ui.btnDownloadEssentialsFiles,
                    'state': self.ui.btnDownloadEssentialsFiles.isEnabled()
                },
                {
                    'ui': self.ui.btnSetOutputFolder,
                    'state': self.ui.btnSetOutputFolder.isEnabled()
                },
                {
                    'ui': self.ui.btnOpenRomFolder,
                    'state': self.ui.btnOpenRomFolder.isEnabled()
                },
                {
                    'ui': self.ui.labelSearch,
                    'state': self.ui.labelSearch.isEnabled()
                },
                {
                    'ui': self.ui.inputSearch,
                    'state': self.ui.inputSearch.isEnabled()
                },
                {
                    'ui': self.ui.btnDownloadRom,
                    'state': self.ui.btnDownloadRom.isEnabled()
                },
                {
                    'ui': self.ui.btnHelp,
                    'state': self.ui.btnHelp.isEnabled()
                },
                {
                    'ui': self.ui.btnPreviousImage,
                    'state': self.ui.btnPreviousImage.isEnabled()
                },
                {
                    'ui': self.ui.labelGameImage,
                    'state': self.ui.labelGameImage.isEnabled()
                },
                {
                    'ui': self.ui.btnNextImage,
                    'state': self.ui.btnNextImage.isEnabled()
                },
                {
                    'ui': self.ui.labelGameName,
                    'state': self.ui.labelGameName.isEnabled()
                },
                {
                    'ui': self.ui.labelImageNumber,
                    'state': self.ui.labelImageNumber.isEnabled()
                },
                {
                    'ui': self.ui.labelAuthorsHeader,
                    'state': self.ui.labelAuthorsHeader.isEnabled()
                },
                {
                    'ui': self.ui.labelAuthors,
                    'state': self.ui.labelAuthors.isEnabled()
                },
                {
                    'ui': self.ui.btnSidebarDownload,
                    'state': self.ui.btnSidebarDownload.isEnabled()
                },
                {
                    'ui': self.ui.btnUpdateInfo,
                    'state': self.ui.btnUpdateInfo.isEnabled()
                },
                {
                    'ui': self.ui.btnOpenZip,
                    'state': self.ui.btnOpenZip.isEnabled()
                },
                {
                    'ui': self.ui.btnVisitWebsite,
                    'state': self.ui.btnVisitWebsite.isEnabled()
                },
                {
                    'ui': self.ui.tableWidget,
                    'state': self.ui.tableWidget.isEnabled()
                },
                {
                    'ui': self.ui.textDescription,
                    'state': self.ui.textDescription.isEnabled()
                }
            ]
            self.buttonStates = states
            # DISABLE EVERYTHING
            for x in self.buttonStates:
                x['ui'].setEnabled(False)

        if boolean == True:
            for x in self.buttonStates:
                x['ui'].setEnabled(x['state'])
            # FIX ESSENTIALS
            if self.disableDownloadEssentials == 1:
                self.ui.btnDownloadEssentialsFiles.setEnabled(False)

    def checkForEssentialFiles(self):
        if os.path.isfile(self.currentDir+'/data/Super Mario World (USA).sfc'):
            self.disableDownloadEssentials = 1
            self.ui.btnDownloadEssentialsFiles.setEnabled(False)
            self.ui.btnDownloadEssentialsFiles.setText(
                'Essential files downloaded')
            print('Essentials button disabled!')
        else:
            self.ui.btnDownloadEssentialsFiles.setEnabled(True)
            self.ui.btnDownloadEssentialsFiles.setText(
                'Download Essential Files')

    def updateConsole(self, text):
        if text == 'reset':
            self.ui.label.setText('SMW: Simple Patcher - by Propagandalf')
            return
        self.ui.label.setText(text)

    def updateProgressBar(self, newValue):
        try:
            currentValue = self.ui.progressBar.value()
            if newValue > int(currentValue):
                self.anim = QtCore.QPropertyAnimation(
                    self.ui.progressBar, b"value")
                self.anim.setDuration(300)
                self.anim.setStartValue(int(currentValue))
                self.anim.setEndValue(int(newValue))
                self.anim.start()
            else:
                self.anim.stop()
                self.ui.progressBar.setValue(0)
        except:
            self.ui.progressBar.setValue(0)

    def helpDialog(self):
        helpDialog().exec()

    def openRomFolder(self):
        try:
            outputFolder = self.getSetting(
                'outputFolder').replace('/', '\\')
            if outputFolder:
                print(outputFolder)
                subprocess.Popen('explorer "{}"'.format(
                    outputFolder))
        except:
            print('Output folder not set. Please select a folder.')

    def messageBox(self, message, title="", type="", buttons=False):
        # CHECK TYPE TO CHANGE ICON
        msg = QMessageBox()
        msg.setWindowIcon(QtGui.QIcon(':/img/icon.png'))
        if type == 'information':
            msg.setIconPixmap(QPixmap(':/img/tap.png'))
        elif type == 'warning':
            msg.setIconPixmap(QPixmap(':/img/warning.png'))
        elif type == 'error':
            msg.setIconPixmap(QPixmap(':/img/error.png'))
        elif type == 'success':
            msg.setIconPixmap(QPixmap(':/img/checkbox.png'))
        elif type == 'cancel':
            msg.setIconPixmap(QPixmap(':/img/cancel.png'))
        elif type == 'checklist':
            msg.setIconPixmap(QPixmap(':/img/checklist.png'))

        if buttons == True:
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        msg.setWindowTitle(title)
        msg.setText(message)
        output = msg.exec_()

        # OUTPUTS
        if output == 1024:
            return True
        else:
            return False

    def getCheckedList(self):
        checked_list = []
        for i in range(self.ui.tableWidget.rowCount()):
            checked = self.ui.tableWidget.item(i, 14).checkState()
            if checked == 2:
                a = {
                    'link': self.ui.tableWidget.item(i, 13).text(),
                    'name': self.ui.tableWidget.item(i, 2).text(),
                    'id': self.ui.tableWidget.item(i, 0).text()
                }
                checked_list.append(a)
        return checked_list

    def openGithub(self):
        try:
            webbrowser.open_new_tab(self.githubLink)
        except:
            print('Could not open Github link...')

    ##################
    ### TABLE LIST ###
    ##################
    def initTable(self):
        # SET TABLE HEADER WIDTH (SHOW)
        self.ui.tableWidget.setColumnWidth(0, 0)       # ID
        self.ui.tableWidget.setColumnWidth(1, 155)     # DATE
        self.ui.tableWidget.setColumnWidth(2, 315)     # NAME
        self.ui.tableWidget.setColumnWidth(3, 100)     # TYPE
        self.ui.tableWidget.setColumnWidth(4, 60)      # EXITS
        self.ui.tableWidget.setColumnWidth(5, 60)      # RATING
        self.ui.tableWidget.setColumnWidth(6, 58)      # TRUSTED
        self.ui.tableWidget.setColumnWidth(7, 60)      # DOWNLOADS
        self.ui.tableWidget.setColumnWidth(8, 0)       # UPDATED
        self.ui.tableWidget.setColumnHidden(8, 1)      # UPDATED (HIDE)
        self.ui.tableWidget.setColumnWidth(9, 55)      # DEMO
        self.ui.tableWidget.setColumnWidth(10, 70)     # FEATURED
        self.ui.tableWidget.setColumnWidth(11, 0)      # AUTHORS
        self.ui.tableWidget.setColumnHidden(11, 1)     # AUTHORS (HIDE)
        self.ui.tableWidget.setColumnWidth(12, 105)    # SIZE
        self.ui.tableWidget.setColumnWidth(13, 0)      # LINK
        self.ui.tableWidget.setColumnHidden(13, 1)     # LINK (HIDE)
        self.ui.tableWidget.setColumnWidth(14, 1)     # MULTIDOWNLOAD

        # CENTER COLUMNS
        delegate = AlignDelegate(self.ui.tableWidget)
        self.ui.tableWidget.setItemDelegateForColumn(1, delegate)   # DATE
        self.ui.tableWidget.setItemDelegateForColumn(4, delegate)   # EXITS
        self.ui.tableWidget.setItemDelegateForColumn(5, delegate)   # RATING
        self.ui.tableWidget.setItemDelegateForColumn(6, delegate)   # TRUSTED
        # self.tableWidget.setItemDelegateForColumn(7, delegate) # DOWNLOADS
        self.ui.tableWidget.setItemDelegateForColumn(9, delegate)   # DEMO
        self.ui.tableWidget.setItemDelegateForColumn(10, delegate)  # FEATURED
        self.ui.tableWidget.setItemDelegateForColumn(12, delegate)  # SIZE
        self.ui.tableWidget.setItemDelegateForColumn(14, delegate)  # SELECT

    def onLeftClick(self):
        try:
            index = self.getListIndex()
            if (isinstance(index.row(), int)):
                id = index.sibling(index.row(), 0).data()
            if self.selectedId == id:
                print('Selected ID:', id, '(already selected)')
            else:
                print('Selected ID:', id)
                self.selectedId = id
        except:
            return

        # RESET
        self.ui.labelGameName.setText('')
        self.ui.labelImageNumber.setText('')

        # ACTIVATE SIDEBAR DOWNLOAD AND OPEN WEB
        self.ui.btnSidebarDownload.setEnabled(True)
        self.ui.btnUpdateInfo.setEnabled(True)
        self.ui.btnVisitWebsite.setEnabled(True)
        self.ui.btnDownloadRom.setEnabled(True)

        # GET IF FOLDER EXISTS (BUTTON ACTIVATED)
        if os.path.isdir(self.currentDir+'/data/hacks/'+id):
            self.ui.btnOpenZip.setEnabled(True)
        else:
            self.ui.btnOpenZip.setEnabled(False)

        # GET AUTHORS & NAME
        index = self.getListIndex()
        try:
            if (isinstance(index.row(), int)):
                author = index.sibling(index.row(), 11).data()
                name = index.sibling(index.row(), 2).data()
                if len(name) > 37:
                    name = name[:35] + '...'
                self.ui.labelAuthorsHeader.setEnabled(True)
                self.ui.labelAuthors.setText(author)
                self.ui.labelGameName.setText(name)
            else:
                self.ui.labelAuthorsHeader.setEnabled(False)
                self.ui.labelAuthors.setText('')
                self.ui.labelGameName.setText('')
        except:
            return

        # GRAB INFO
        startWorker = 0

        # GET IMAGES
        imgPath = self.currentDir+'/data/images/'+id
        if os.path.isdir(imgPath):
            # GRAB ALL IMAGES
            pngFiles = []
            for dirpath, dirnames, filenames in os.walk(imgPath):
                for filename in [f for f in filenames if f.endswith(".png")]:
                    pngFiles.append(os.path.join(dirpath, filename))
            if pngFiles:
                # SET VARIABLE
                self.gamePics = pngFiles
                pngImage = QPixmap(pngFiles[0])
                self.gamePicsId = 0
                self.ui.labelGameImage.setPixmap(pngImage)
                self.ui.labelGameImage.setEnabled(True)
                self.ui.btnPreviousImage.setEnabled(True)
                self.ui.btnNextImage.setEnabled(True)
                # ADD IMAGE NUMBER + LENGHT
                amountOfImages = len(pngFiles)
                output = '[{}/{}]'.format('1', amountOfImages)
                self.ui.labelImageNumber.setText(output)
            else:
                startWorker = 1
                self.gamePicsId = None
                self.ui.labelGameImage.clear()
                self.ui.labelImageNumber.setText('')
                self.ui.labelGameImage.setText('Loading images...')
                self.ui.labelGameImage.setEnabled(False)
                self.ui.btnPreviousImage.setEnabled(False)
                self.ui.btnNextImage.setEnabled(False)
        else:
            startWorker = 1
            self.gamePicsId = None
            self.ui.labelGameImage.clear()
            self.ui.labelGameImage.setText('Loading images...')
            self.ui.labelGameImage.setEnabled(False)
            self.ui.btnPreviousImage.setEnabled(False)
            self.ui.btnNextImage.setEnabled(False)

        # GET DESCRIPTION
        desc = self.getDescription(id)
        if desc == None:
            startWorker = 1
            self.ui.textDescription.setText('')
        else:
            self.ui.textDescription.setText(desc)

        # START WORKER TO GRAB INFORMATION
        if startWorker == 1:
            self.workerGetMoreInfo(id)

    def loadDataToList(self, list):
        if list == None:
            print('No items in database. Please update your list.')
            return
        row = 0
        # print('LIST OF ITEMS:', len(list))
        self.ui.tableWidget.setRowCount(len(list))
        self.ui.tableRowCount = len(list)

        for item in list:
            romID = str(item[1])
            romName = str(item[3])
            romDate = str(item[4][:-3].replace('-',
                          '.').replace(' ', ' [') + ']')
            if item[5] == 'Yes':
                romDemo = 'Yes'
            else:
                romDemo = '-'
            if item[6] == 'Yes':
                romFeatured = 'Yes'
            else:
                romFeatured = '-'
            romLength = str(item[7])
            if 'Standard:' in str(item[8]):
                romType = str(item[8])[10:]
            elif 'Kaizo:' in str(item[8]):
                romType = str(item[8])
            elif 'Misc.:' in str(item[8]):
                romType = str(item[8])[7:]
            else:
                romType = str(item[8])
            romAuthors = str(item[9])
            if item[10] == 'None':
                romRating = '-'
            else:
                romRating = str(item[10])
            if 'KiB' in item[11]:
                size = self.formatFileSize(float(item[11][:-4]), 'KB', 'MB', 4)
                romSize = str(size) + ' MiB'
            else:
                size = "{:.4f}".format(float(item[11][:-4]))
                romSize = str(size) + ' MiB'
            romLink = str(item[12])
            romDownloads = str(item[13])
            if item[14] == 1:
                romModerated = 'Yes'
            else:
                romModerated = '-'
            romUpdated = item[15]
            # UPDATE LIST
            self.ui.tableWidget.setItem(
                row, 0, QtWidgets.QTableWidgetItem(romID))
            self.ui.tableWidget.setItem(
                row, 1, QtWidgets.QTableWidgetItem(romDate))
            self.ui.tableWidget.setItem(
                row, 2, QtWidgets.QTableWidgetItem(romName))
            self.ui.tableWidget.setItem(
                row, 3, QtWidgets.QTableWidgetItem(romType))
            self.ui.tableWidget.setItem(
                row, 4, QtWidgets.QTableWidgetItem(romLength))
            self.ui.tableWidget.setItem(
                row, 5, QtWidgets.QTableWidgetItem(romRating))
            self.ui.tableWidget.setItem(
                row, 6, QtWidgets.QTableWidgetItem(romModerated))
            self.ui.tableWidget.setItem(
                row, 7, QtWidgets.QTableWidgetItem(romDownloads))
            self.ui.tableWidget.setItem(
                row, 8, QtWidgets.QTableWidgetItem(romUpdated))
            self.ui.tableWidget.setItem(
                row, 9, QtWidgets.QTableWidgetItem(romDemo))
            self.ui.tableWidget.setItem(
                row, 10, QtWidgets.QTableWidgetItem(romFeatured))
            self.ui.tableWidget.setItem(
                row, 11, QtWidgets.QTableWidgetItem(romAuthors))
            self.ui.tableWidget.setItem(
                row, 12, QtWidgets.QTableWidgetItem(romSize))
            self.ui.tableWidget.setItem(
                row, 13, QtWidgets.QTableWidgetItem(romLink))
            # ADD CHECKBOX
            chkBoxItem = QtWidgets.QTableWidgetItem()
            chkBoxItem.setFlags(
                QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            self.ui.tableWidget.setItem(row, 14, chkBoxItem)
            row += 1

    def removeDataFromList(self):
        for i in reversed(range(self.ui.tableWidget.rowCount())):
            self.ui.tableWidget.removeRow(i)

    def getListIndex(self):
        try:
            index = self.ui.tableWidget.selectionModel().selectedRows()[0]
            return index
        except:
            return False

    def updateInfo(self):
        try:
            index = self.getListIndex()
            if (isinstance(index.row(), int)):
                id = index.sibling(index.row(), 0).data()
            self.workerGetMoreInfo(id)
        except:
            return

    ###############
    ### WORKERS ###
    ###############
    def workerGetMoreInfo(self, id):
        self.ui.textDescription.setText('')
        self.worker = WThreadGetMoreInfo(id)
        self.worker.start()
        self.worker.finished.connect(self.finishWorkerGetMoreInfo)
        self.worker.update_delete.connect(self.updateDeleteId)
        self.worker.update_progress.connect(self.updateProgressBar)
        self.worker.update_console.connect(self.updateConsole)
        self.worker.update_images.connect(self.updateImages)
        self.worker.update_description.connect(self.updateDescription)

    def workerUpdateDatabase(self):
        self.setButtonsEnabled(False)
        self.worker = WThreadUpdateDatabase()
        self.worker.start()
        self.worker.finished.connect(self.finishWorkerUpdateDatabase)
        self.worker.update_progress.connect(self.updateProgressBar)
        self.worker.update_console.connect(self.updateConsole)
        self.worker.update_hack.connect(self.dbUpdateRom)

    def workerDownloadEssentials(self):
        self.setButtonsEnabled(False)
        self.worker = WThreadDownloadEssentials()
        self.worker.start()
        self.worker.finished.connect(self.finishWorkerDownloadEssentials)
        self.worker.update_progress.connect(self.updateProgressBar)
        self.worker.update_console.connect(self.updateConsole)

    def workerDownloadAndPatchRom(self):
        outputFolder = self.getSetting('outputFolder')
        if outputFolder == None:
            self.messageBox('You need to select an output folder before you can download any files.',
                            'Error', 'warning')
            print(
                'You need to select an output folder before you can download any hacks...')
            return False
        if not os.path.isfile(self.currentDir+'/data/Super Mario World (USA).sfc'):
            self.messageBox('The essential files was not found.\nMake sure to download the files before\nyou download and patch any hacks.',
                            'Error', 'warning')
            print('You need to download the essential files.')
            return False
        index = self.getListIndex()
        try:
            if (isinstance(index.row(), int)):
                link = index.sibling(index.row(), 13).data()
                name = index.sibling(index.row(), 2).data()
                id = index.sibling(index.row(), 0).data()
        except:
            print('No row selected...')
            return
        dlList = [
            {
                'link': link,
                'name': name,
                'id': id
            }
        ]
        self.setButtonsEnabled(False)
        self.worker = WThreadDownloadAndPatchRom(dlList, outputFolder)
        self.worker.start()
        self.worker.finished.connect(self.finishWorkerDownloadAndPatchRom)
        self.worker.update_progress.connect(self.updateProgressBar)
        self.worker.update_console.connect(self.updateConsole)
        self.worker.update_zip.connect(self.updateZip)

    def workerDownloadAndPatchRoms(self):
        outputFolder = self.getSetting('outputFolder')
        if outputFolder == None:
            self.messageBox('You need to select an output folder before you can download any files.',
                            'Error', 'warning')
            print(
                'You need to select an output folder before you can download any hacks...')
            return False
        if not os.path.isfile(self.currentDir+'/data/Super Mario World (USA).sfc'):
            self.messageBox('The essential files was not found.\nMake sure to download the files before\nyou download and patch any hacks.',
                            'Error', 'warning')
            print('You need to download the essential files.')
            return False
        rows = self.getCheckedList()
        if not rows:
            self.messageBox('You have not checked any checkboxes.',
                            'Error', 'checklist')
            return
        dlList = []
        for item in rows:
            dlList.append(item)
        self.setButtonsEnabled(False)
        self.worker = WThreadDownloadAndPatchRom(dlList, outputFolder)
        self.worker.start()
        self.worker.finished.connect(self.finishWorkerDownloadAndPatchRom)
        self.worker.update_progress.connect(self.updateProgressBar)
        self.worker.update_console.connect(self.updateConsole)
        self.worker.update_zip.connect(self.updateZip)

    ######################
    ### WORKER FINISHED ###
    ######################
    def finishWorkerUpdateDatabase(self):
        # RELOAD TABLE
        self.removeDataFromList()
        data = self.getAllHacks()
        self.loadDataToList(data)
        # ENABLE BUTTONS AND FIX PROGRESSBAR / CONSOLE
        self.ui.inputSearch.setPlainText('')
        self.setButtonsEnabled(True)
        self.ui.progressBar.setValue(0)
        self.updateConsole('reset')

    def finishWorkerDownloadEssentials(self):
        self.checkForEssentialFiles()
        self.setButtonsEnabled(True)
        self.updateProgressBar(0)
        self.updateConsole('reset')

    def finishWorkerDownloadAndPatchRom(self):
        print('DOWNLOAD AND PATCH COMPLETE')
        self.setButtonsEnabled(True)
        self.updateProgressBar(0)
        self.updateConsole('reset')

    def finishWorkerGetMoreInfo(self):
        pass

    ########################
    ### WORKER FUNCTIONS ###
    ########################
    def updateDescription(self, desc):
        # UPDATE DESCRIPTION
        try:
            id = desc['id']
            description = desc['description']
            self.setDescription(id, description)
        except:
            print('Could not insert description to ROM ID')
            return False
        # CHECK IF ROW STILL IS SELECTED
        try:
            index = self.getListIndex()
            if (isinstance(index.row(), int)):
                id = index.sibling(index.row(), 0).data()
            if str(id) != str(desc['id']):
                return
            # UPDATE DESCRIPTION
            self.ui.textDescription.setText(description)
        except:
            pass

    def updateImages(self, images):
        # CHECK IF ROW STILL IS SELECTED
        try:
            index = self.getListIndex()
            if (isinstance(index.row(), int)):
                id = index.sibling(index.row(), 0).data()
            if str(id) != str(images[0]['id']):
                print('SAME ROW NOT SELECTED. NOT UPDATING IMAGES.')
                return
        except:
            return
        # UPDATE IMAGES
        try:
            imgs = []
            for img in images:
                imgs.append(img['image'])
            self.gamePics = imgs
            pngImage = QPixmap(imgs[0])
            self.gamePicsId = 0
            self.ui.labelGameImage.setPixmap(pngImage)
            self.ui.labelGameImage.setEnabled(True)
            self.ui.btnPreviousImage.setEnabled(True)
            self.ui.btnNextImage.setEnabled(True)
            self.ui.labelImageNumber.setText(
                '[{}/{}]'.format('1', str(len(imgs))))
        except:
            print('Could not update images.')

    def updateZip(self, inputId):
        try:
            index = self.getListIndex()
            if (isinstance(index.row(), int)):
                id = index.sibling(index.row(), 0).data()
            if str(id) != str(inputId):
                return
            else:
                buttonStates = []
                for x in self.buttonStates:
                    ui = x['ui']
                    if ui.objectName() == 'btnOpenZip':
                        state = True
                    else:
                        state = x['state']
                    a = {
                        'ui': ui,
                        'state': state
                    }
                    buttonStates.append(a)
                self.buttonStates = buttonStates
            # print(self.buttonStates)
        except:
            print('Error updating ZIP button')

    def updateDeleteId(self, gameId):
        print(gameId)
        # DELETE POST
        if self.conn is not None:
            try:
                self.conn.execute(
                    "DELETE FROM hacks WHERE gameid=?", (gameId, ))
                self.conn.commit()
            except:
                return None
        # RESET
        self.ui.labelGameImage.clear()
        self.ui.labelGameName.setText('')
        self.ui.labelImageNumber.setText('')
        self.ui.textDescription.setText('')
        self.ui.labelAuthors.setText('')
        # DISABLE
        self.ui.btnNextImage.setEnabled(False)
        self.ui.btnPreviousImage.setEnabled(False)
        self.ui.labelAuthorsHeader.setEnabled(False)
        self.ui.btnSidebarDownload.setEnabled(False)
        self.ui.btnUpdateInfo.setEnabled(False)
        self.ui.btnOpenZip.setEnabled(False)
        self.ui.btnVisitWebsite.setEnabled(False)
        # RELOAD TABLE
        self.removeDataFromList()
        data = self.getAllHacks()
        self.loadDataToList(data)
        # FIX PROGRESSBAR / CONSOLE
        self.ui.inputSearch.setPlainText('')
        self.ui.progressBar.setValue(0)
        # MESSAGE USER
        self.messageBox('The game with ID: '+gameId +
                        ' is no longer available.\nIt has now been removed from the database.', 'File not found', 'error')

    ################
    ### DATABASE ###
    ################
    def initDatabase(self):
        # CREATE FOLDER
        try:
            if self.currentOS == 'Windows':
                os.makedirs(self.currentDir+'/data', exist_ok=True)
            if self.currentOS == 'MacOS':
                os.makedirs(self.currentDir+'/data')
            if self.currentOS == 'Linux':
                os.makedirs(self.currentDir+'/data')
        except OSError as err:
            pass
        # CREATE DATABASE AND CONNECT
        try:
            self.conn = sqlite3.connect(self.currentDir+'/data' + self.dbFile)
            self.conn.execute("PRAGMA foreign_keys = 1")
        except sqlite3.Error as e:
            print('Could not connect to database.', e)
        # CREATE SQL TABLES
        if self.conn is not None:
            sqlHacks = """ CREATE TABLE IF NOT EXISTS hacks (
                            hid integer PRIMARY KEY,
                            gameid integer NOT NULL,
                            description text,
                            name text NOT NULL,
                            date text NOT NULL,
                            demo text NOT NULL,
                            featured integer NOT NULL DEFAULT 0,
                            length integer NOT NULL,
                            type text NOT NULL,
                            authors text NOT NULL,
                            rating text NOT NULL,
                            size text NOT NULL,
                            linkDownload text NOT NULL,
                            downloads integer NOT NULL,
                            approved integer NOT NULL,
                            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            downloaded integer
                        ); """
            sqlSettings = """ CREATE TABLE IF NOT EXISTS settings (
                            id integer PRIMARY KEY,
                            key text NOT NULL,
                            value text NOT NULL
                        ); """

            # GENERATE TABLES IF NOT EXIST
            self.createTable(sqlHacks)
            self.createTable(sqlSettings)

    def disconnect(self):
        print('Closing down database.')
        self.conn.close()

    def createTable(self, sqlTable):
        try:
            c = self.conn.cursor()
            c.execute(sqlTable)
        except sqlite3.Error as e:
            print('Could not create table in database.', e)

    def dbUpdateRom(self, data):
        if self.conn is not None:
            # CHECK IF CURRENT POST ONLY SHOULD BE UPDATED...
            try:
                cursor = self.conn.execute(
                    "SELECT * FROM hacks WHERE gameid=?", (data['gameid'], ))
                row = cursor.fetchone()
                if row:
                    # UPDATE GAME
                    try:
                        now = datetime.datetime.now()
                        dateAndTime = now.strftime("%Y-%m-%d %H:%M:%S")
                        cursor = self.conn.execute(
                            "UPDATE hacks SET name=?, date=?, demo=?, featured=?, length=?, type=?, authors=?, rating=?, size=?, linkDownload=?, downloads=?, approved=?, updated_at=? WHERE gameid=?", (data['name'], data['date'], data['demo'], data['featured'], data['length'], data['type'], data['authors'], data['rating'], data['size'], data['link'], data['downloads'], data['approved'], dateAndTime, data['gameid']))
                        self.conn.commit()
                        print('Successfully updated:', data['name'])
                        return True
                    except:
                        self.conn.rollback()
                        print('Failed to update rom:', data['name'])
                        return False
            except:
                pass
            # IF POST DOES NOT EXIST, INSERT NEW DATA
            try:
                cursor = self.conn.cursor()
                id = self.conn.execute(
                    "insert into hacks (gameid, name, date, demo, featured, length, type, authors, rating, size, linkDownload, downloads, approved) values(?,?,?,?,?,?,?,?,?,?,?,?,?)", (data['gameid'], data['name'], data['date'], data['demo'], data['featured'], data['length'], data['type'], data['authors'], data['rating'], data['size'], data['link'], data['downloads'], data['approved']))
                self.conn.commit()
                print('Successfully added:', data['name'])
                return True
            except sqlite3.Error as error:
                self.conn.rollback()
                print("Failed to add romhack...", error)
                return False
        else:
            print('Conn is NONE!')

    def getAllHacks(self, column='date', direction='DESC'):
        if self.conn is not None:
            try:
                rows = []
                cursor = self.conn.execute(
                    "SELECT * FROM hacks ORDER BY {} {}".format(column, direction))
                rows = cursor.fetchall()
                if rows:
                    s = {
                        'column': column,
                        'direction': direction
                    }
                    self.sort = s
                    return rows
            except:
                return False

    def getSetting(self, key):
        if self.conn is not None:
            try:
                cursor = self.conn.execute(
                    "SELECT * FROM settings WHERE key=?", (key, ))
                row = cursor.fetchone()
                if row:
                    return row[2]
                else:
                    return None
            except:
                return None

    def setSetting(self, key, value):
        if self.conn is not None:
            try:
                cursor = self.conn.execute(
                    "SELECT * FROM settings WHERE key=?", (key, ))
                row = cursor.fetchone()
                if row:
                    # UPDATE GAME
                    try:
                        cursor = self.conn.execute(
                            "UPDATE settings SET key=?, value=? WHERE key=?", (key, value, key))
                        self.conn.commit()
                        print('Successfully updated setting:', key, value)
                        return True
                    except:
                        self.conn.rollback()
                        print('Failed to update setting:', key, value)
                        return None
            except:
                pass
            # IF POST DOES NOT EXIST, INSERT NEW DATA
            try:
                cursor = self.conn.cursor()
                self.conn.execute(
                    "insert into settings (key, value) values(?,?)", (key, value))
                self.conn.commit()
                print('Successfully added settings:', key, value)
                return True
            except sqlite3.Error as error:
                self.conn.rollback()
                print("Failed to add settings...", error)
                return None
        else:
            print('Conn is NONE!')

    def getDescription(self, gameid):
        if self.conn is not None:
            try:
                cursor = self.conn.execute(
                    "SELECT * FROM hacks WHERE gameid=?", (gameid, ))
                row = cursor.fetchone()
                if row:
                    return row[2]
                else:
                    return None
            except:
                return None

    def setDescription(self, romid, desc):
        if self.conn is not None:
            try:
                cursor = self.conn.execute(
                    "SELECT * FROM hacks WHERE gameid=?", (romid, ))
                row = cursor.fetchone()
                if row:
                    # UPDATE DESC
                    try:
                        cursor = self.conn.execute(
                            "UPDATE hacks SET description=? WHERE gameid=?", (desc, romid))
                        self.conn.commit()
                        print('Successfully updated description:', romid)
                        return True
                    except:
                        self.conn.rollback()
                        print('Failed to update description:', romid)
                        return None
            except:
                pass
        else:
            print('Conn is NONE!')


######################
### WORKER THREADS ###
######################
class WThreadUpdateDatabase(QtCore.QThread):
    update_progress = QtCore.pyqtSignal(int)
    update_console = QtCore.pyqtSignal(str)
    update_hack = QtCore.pyqtSignal(dict)
    currentDir = None
    amountWaiting = None
    lastPage = None

    def __init__(self):
        super(WThreadUpdateDatabase, self).__init__()
        self.currentDir = self.getCurrentDir()
        self.getStartInformation()

    def run(self):
        self.updateDatabase()

    def getStartInformation(self):
        # GETS LAST PAGE & AMOUNT WAITING
        print('Trying to get last page and amount waiting... Please wait')
        try:
            htmlPage = 'https://www.smwcentral.net/?p=section&s=smwhacks'
            source = requests.get(htmlPage).text            
            soup = bs.BeautifulSoup(source, 'html.parser')
            tablerow = soup.find('div', class_="actions")
            # GET AMOUNT WAITING
            result = re.search('waiting (.*)</a>', str(tablerow))
            self.amountWaiting = int(result.group(1)[1:-1])
            print('Awaiting romhacks:', self.amountWaiting)
            # GET LAST PAGE
            pagesHeader = soup.find('ul', class_="page-list")
            liTags = pagesHeader.findAll('li')
            result = re.search('">(.*)</a>', str(liTags[-1]))
            self.lastPage = result.group(1)
            print('Amount of pages:', self.lastPage)
            return True
        except:
            print('Could not grab information from SMWC.')
            return False

    def getHtmlPage(self, page, *args):
        waiting = '&u=0&g=0&n='  # APPROVED
        try:
            if args[0] == 'waiting':
                waiting = '&u=1&g=0&n='
        except:
            pass
        bHtml = 'https://www.smwcentral.net/?p=section&s=smwhacks'+waiting
        aHtml = '&o=date&d=desc'
        output = bHtml+str(page)+aHtml
        return output

    def updateDatabase(self):
        # LOOP THRU ALL APPROVED
        print('Extracting approved romhacks!')
        if self.lastPage != None:
            for page in range(1, int(self.lastPage)+1):
                print('Grabbing information from page:', str(page))
                self.sendConsole(
                    'Updating database - '+str(page)+'/'+str(int(self.lastPage)+1))
                self.sendProgressBar(page, int(self.lastPage)+1)
                # GET ALL ROWS AND INSERT THEM TO VARIABLE HACKS
                try:
                    # INSERT PAGE HERE LATER INSIDE LOOP
                    source = requests.get(self.getHtmlPage(page)).text
                    result = source.split('<div class="content has-table">')[
                        1]
                    result = result.split('<tbody>')[1].split('</tbody>')[0]                    
                    soup = bs.BeautifulSoup(result, 'html.parser')
                    tablerows = soup.findAll('tr')
                    hacks = []
                    for i in range(1, len(tablerows)):
                        hacks.append(str(tablerows[i]))  
                except:
                    print('Could not get information from page:', page)
                # LOOP THRU HACKS AND EXTRACT INFORMATION AND INSERT TO DATABASE
                try:
                    for hack in hacks:
                        soup = bs.BeautifulSoup(hack, 'html.parser')
                        tds = soup.findAll('td')
                        # [0] NAME, ID, DATE
                        romName = str(tds[0].find('a').text).strip()
                        romId = str(tds[0]).split('id=')[
                            1].split('">')[0].strip()
                        romDate = str(tds[0]).split('<time datetime="')[
                            1].split('">')[0].strip().replace('T', ' ')
                        # [1] DEMO
                        romDemo = str(tds[1].text).strip()
                        # [2] FEATURED
                        romFeatured = str(tds[2].text).strip()
                        # [3] LENGTH                        
                        romLength = str(tds[3].text).strip()[:-8]
                        # [4] TYPE                        
                        romType = str(tds[4].text).strip()
                        # [5] AUTHORS
                        romAuthors = str(tds[5].text).strip()
                        # [6] RATING
                        romRating = str(tds[6].text).strip()
                        # [7] SIZE
                        romSize = str(tds[7].text).strip()
                        # [8] DOWNLOADLINK, DOWNLOADS
                        romDl = str(tds[8]).split('<a href="')[
                            1].split('">Download</a>')[0].strip()
                        romDownloads = str(tds[8]).split('class="secondary-info">')[
                            1].split(' downlo')[0].strip().replace(',', '')                        
                        data = {
                            'name': romName,
                            'gameid': romId,
                            'date': romDate,
                            'demo': romDemo,
                            'featured': romFeatured,
                            'length': romLength,
                            'type': romType,
                            'authors': romAuthors,
                            'rating': romRating,
                            'size': romSize,
                            'downloads': romDownloads,
                            'link': romDl,
                            'approved': 1
                        }
                        print(data['link'])
                        # INSERT IN TO DATABASE
                        self.dbSendUpdate(data)
                except:
                    print('Something went wrong fetching the data.')
                randomSecs = random.randint(1, 2)
                print('Page:', '['+str(page)+'/'+str(self.lastPage)+'] [APPROVED ROMHACKS] Complete!',
                      'Sleeping for', str(randomSecs), 'seconds...')
                # time.sleep(randomSecs)
        else:
            print('Failed to extract information due to LastPage not set.')
            return

        # EXTRACTING NON APPROVED ROMHACKS!
        print('Extracting non approved romhacks!')
        self.sendConsole(
            'Updating database - '+str(int(self.lastPage)+1)+'/'+str(int(self.lastPage)+1))
        self.sendProgressBar(int(self.lastPage)+1, int(self.lastPage)+1)
        try:
            source = requests.get(self.getHtmlPage(1, 'waiting')).text
            result = source.split('<div id="list_content">')[
                1].split('</table>')[0]
            result = result[23:]+'</table>'
            final = result.replace('</div>', '')
            soup = bs.BeautifulSoup(final, 'html.parser')
            tablerows = soup.findAll('tr')
            hacks = []
            for i in range(1, len(tablerows)):
                hacks.append(str(tablerows[i]))
        except:
            print('Could not get information from page:', page)
        # LOOP THRU HACKS AND EXTRACT INFORMATION AND INSERT TO DATABASE
        try:
            for hack in hacks:
                soup = bs.BeautifulSoup(hack, 'html.parser')
                tds = soup.findAll('td')
                # [0] NAME, ID, DATE
                romName = str(tds[0].find('a').text).strip()
                romId = str(tds[0]).split('id=')[
                    1].split('">')[0].strip()
                romDate = str(tds[0]).split('<time datetime="')[
                    1].split('">')[0].strip().replace('T', ' ')
                # [1] DEMO
                romDemo = str(tds[1].text).strip()
                # [2] FEATURED
                romFeatured = str(tds[2].text).strip()
                # [3] LENGTH
                romLength = str(tds[3].text).strip()[:-8]
                # [4] TYPE
                romType = str(tds[4].text).strip()
                # [5] AUTHORS
                romAuthors = str(tds[5].text).strip()
                # [6] RATING
                romRating = str(tds[6].text).strip()
                # [7] SIZE
                romSize = str(tds[7].text).strip()
                # [8] DOWNLOADLINK, DOWNLOADS
                romDl = 'https:'+str(tds[8]).split('<a href="')[
                    1].split('">Download</a>')[0].strip()
                romDownloads = str(tds[8]).split('class="small">')[
                    1].split(' downloads')[0].strip().replace(',', '')
                data = {
                    'name': romName,
                    'gameid': romId,
                    'date': romDate,
                    'demo': romDemo,
                    'featured': romFeatured,
                    'length': romLength,
                    'type': romType,
                    'authors': romAuthors,
                    'rating': romRating,
                    'size': romSize,
                    'downloads': romDownloads,
                    'link': romDl,
                    'approved': 0
                }
                # print(data)
                # INSERT IN TO DATABASE
                self.dbSendUpdate(data)
        except:
            print('Something went wrong fetching the data.')
        print('Page:', '[1/1] [NON APPROVED ROMHACKS] Complete!')
        self.sendConsole('Almost done...')
        self.sendProgressBar(1, 1)

    def dbSendUpdate(self, data):
        self.update_hack.emit(data)

    def sendProgressBar(self, current, total):
        try:
            value = round((current/total)*100)
            self.update_progress.emit(value)
        except:
            pass

    def sendConsole(self, text):
        self.update_console.emit(text)

    def getCurrentDir(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return application_path


class WThreadDownloadEssentials(QtCore.QThread):
    currentDir = None
    currentOS = None
    patcherUrl = 'https://dl.smwcentral.net/11474/floating.zip'
    snesRomUrl = 'https://edgeemu.net/down.php?id=241871'
    update_progress = QtCore.pyqtSignal(int)
    update_console = QtCore.pyqtSignal(str)

    def __init__(self):
        super(WThreadDownloadEssentials, self).__init__()
        self.currentDir = self.getCurrentDir()
        self.getOS()

    def run(self):
        # self.sendConsole('Downloading Floating IPS')
        # self.downloadPatcher()
        self.sendConsole('Downloading Original ROM')
        self.downloadRom()
        self.sendConsole('Download Complete!')
        self.sendProgressBar(1, 1)
        time.sleep(1)
        self.sendConsole('reset')

    def getOS(self):
        curOS = platform.system()
        if curOS == 'Darwin':
            self.currentOS = 'MacOS'
        elif curOS == 'Linux':
            self.currentOS = 'Linux'
        elif curOS == 'Windows':
            self.currentOS = 'Windows'
        else:
            print('Could not get correct system.')
            return False
        print('Currently on:', self.currentOS)

    def createFolder(self, folder):
        # CREATE FOLDER
        try:
            if self.currentOS == 'Windows':
                os.makedirs(self.currentDir+'/data/'+folder, exist_ok=True)
            if self.currentOS == 'MacOS':
                os.makedirs(self.currentDir+'/data/'+folder)
            if self.currentOS == 'Linux':
                os.makedirs(self.currentDir+'/data/'+folder)
            print('Created folder: /data/'+folder)
            return True
        except OSError as err:
            print('Could not create folder: /data/'+folder,
                  'The folder maybe already exist...?')

    def deleteFolder(self, folder):
        try:
            shutil.rmtree(self.currentDir+'/data/'+folder)
            print('Deleted folder: /data/'+folder)
            return True
        except:
            print('Could not delete folder: /data/'+folder,
                  'The folder maybe already deleted...?')
            return False

    def downloadPatcher(self):
        #
        # NOT IN USE ANYMORE!
        #
        # CHECK IF PATCHER ALREADY EXISTS
        if os.path.isfile(self.currentDir+'/data/flips.exe') and os.path.isfile(self.currentDir+'/data/flips-linux'):
            print('Pathcher already exists!')
            return
        try:
            # CREATE TEMP FOLDER
            self.createFolder('temp')
            # DOWNLOAD FILE
            print('Downloading patcher...')
            self.downloadFile(
                self.patcherUrl, self.currentDir+'/data/temp/patcher.zip')
            print('Downloading complete!')
            # UNZIP
            self.sendConsole('Unzipping and moving files...')
            print('Unzipping and moving files...')
            with zipfile.ZipFile(self.currentDir+'/data/temp/patcher.zip', 'r') as zip_ref:
                zip_ref.extractall(self.currentDir+'/data/temp/')
            # COPY ALL IMPORTANT FILES TO DATA FOLDER
            shutil.move(self.currentDir+'/data/temp/flips.exe',
                        self.currentDir+'/data/flips.exe')
            shutil.move(self.currentDir+'/data/temp/flips-linux',
                        self.currentDir+'/data/flips-linux')
            # DELETE FOLDER
            self.deleteFolder('temp')
            print('Successfully downloaded the patcher!')
            return True
        except:
            print('Could not download rom patcher...')
            return False

    def downloadRom(self):
        # CHECK IF PATCHER ALREADY EXISTS
        self.sendProgressBar(1, 5)
        if os.path.isfile(self.currentDir+'/data/Super Mario World (USA).sfc'):
            # help(QtGui)
            print('Rom already exists!')
            return
        try:
            # CREATE TEMP FOLDER
            self.createFolder('temp')
            # DOWNLOAD FILE
            print('Downloading rom...')
            self.sendProgressBar(2, 5)
            self.downloadFile(
                self.snesRomUrl, self.currentDir+'/data/temp/smw.7z')
            print('Downloading complete!')
            # UNZIP (.7z)
            self.sendProgressBar(3, 5)
            self.sendConsole('Unzipping and moving file...')
            print('Unzipping and moving file(s)ss')
            with py7zr.SevenZipFile(self.currentDir+'/data/temp/smw.7z', mode='r') as z:
                z.extractall(self.currentDir+'/data')
            # DELETE FOLDER
            self.sendProgressBar(4, 5)
            self.deleteFolder('temp')
            print('Successfully downloaded Super Mario World (USA).sfc!')
            return True
        except:
            print('Could not download Super Mario World rom...')
            return False

    def downloadFile(self, url, save_path, chunk_size=256):
        r = requests.get(url, stream=True)
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)

    def sendProgressBar(self, current, total):
        try:
            value = round((current/total)*100)
            self.update_progress.emit(value)
        except:
            pass

    def sendConsole(self, text):
        self.update_console.emit(text)

    def getCurrentDir(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return application_path


class WThreadDownloadAndPatchRom(QtCore.QThread):
    currentDir = None
    update_progress = QtCore.pyqtSignal(int)
    update_console = QtCore.pyqtSignal(str)
    update_zip = QtCore.pyqtSignal(str)
    dlList = None
    downloadLink = None
    romName = None
    romId = None
    outputFolder = None
    currentOS = None

    def __init__(self, dlList, outputFolder):
        super(WThreadDownloadAndPatchRom, self).__init__()
        self.currentDir = self.getCurrentDir()
        self.getOS()
        self.dlList = dlList
        self.outputFolder = outputFolder

    def run(self):
        progress = 1
        for dlItem in self.dlList:
            self.downloadLink = dlItem['link']
            self.romName = dlItem['name']
            self.romId = dlItem['id']

            # GET FILENAME
            self.sendConsole('Grabbing information')
            self.sendProgressBar(progress, (6*len(self.dlList)))
            progress += 1
            f = os.path.basename(self.downloadLink)
            filename = urllib.parse.unquote(f)

            # CREATE FOLDER AND DOWNLOAD THE FILE
            self.sendConsole('Downloading BPS file')
            self.sendProgressBar(progress, (6*len(self.dlList)))
            progress += 1
            self.createFolder('hacks/'+self.romId)
            dl = self.downloadFile(self.downloadLink, self.currentDir +
                                   '/data/hacks/'+self.romId+'/'+filename)
            # EXPORT THE CONTENT TO TEMP
            if dl == True:
                self.update_zip.emit(self.romId)
            self.sendConsole('Unzipping files')
            self.sendProgressBar(progress, (6*len(self.dlList)))
            progress += 1
            self.createFolder('temp')
            try:
                with zipfile.ZipFile(self.currentDir+'/data/hacks/'+self.romId+'/'+filename, 'r') as zip_ref:
                    zip_ref.extractall(self.currentDir+'/data/temp/')
            except:
                print('Failed to unzip file. Aborting...')
                self.sendConsole('Failed to unzip file. Aborting...')
                self.sendProgressBar(1, 1)
                time.sleep(1)
                self.deleteFolder('temp')
                self.sendConsole('reset')
                return

            # SEARCH FOR PATCH FILE (MULTIPLE)
            self.sendConsole('Sorting files')
            self.sendProgressBar(progress, (6*len(self.dlList)))
            bpsFiles = []
            for dirpath, dirnames, filenames in os.walk(self.currentDir+'/data/temp/'):
                for filename in [f for f in filenames if f.endswith(".bps")]:
                    # bpsFiles.append(os.path.join(dirpath, filename))
                    f = {
                        'name': os.path.join(filename)[:-4],
                        'path': os.path.join(dirpath, filename)
                    }
                    bpsFiles.append(f)

            # PATCH FILES
            self.sendConsole('Patching ROM file(s)')
            self.sendProgressBar(progress, (6*len(self.dlList)))
            progress += 1
            sourcefile = self.currentDir+'/data/Super Mario World (USA).sfc'
            for patch in bpsFiles:
                self.patchRomFile(
                    sourcefile, patch['path'], self.outputFolder+'/'+patch['name']+'.sfc')

            # RESET
            self.sendConsole('Almost done...')
            self.sendProgressBar(progress, (6*len(self.dlList)))
            progress += 1
            self.deleteFolder('temp')
            self.sendConsole('reset')

        self.sendProgressBar(1, 1)
        time.sleep(0.5)

    def getOS(self):
        curOS = platform.system()
        if curOS == 'Darwin':
            self.currentOS = 'MacOS'
        elif curOS == 'Linux':
            self.currentOS = 'Linux'
        elif curOS == 'Windows':
            self.currentOS = 'Windows'
        else:
            print('Could not get correct system.')
            return False
        print('Currently on:', self.currentOS)

    def createFolder(self, folder):
        # CREATE FOLDER
        try:
            if self.currentOS == 'Windows':
                os.makedirs(self.currentDir+'/data/'+folder, exist_ok=True)
            if self.currentOS == 'MacOS':
                os.makedirs(self.currentDir+'/data/'+folder)
            if self.currentOS == 'Linux':
                os.makedirs(self.currentDir+'/data/'+folder)
            print('Created folder: /data/'+folder)
            return True
        except OSError as err:
            print('Could not create folder: /data/'+folder,
                  'The folder maybe already exist...?')

    def deleteFolder(self, folder):
        try:
            shutil.rmtree(self.currentDir+'/data/'+folder)
            print('Deleted folder: /data/'+folder)
            return True
        except:
            print('Could not delete folder: /data/'+folder,
                  'The folder maybe already deleted...?')

    def downloadFile(self, url, save_path, chunk_size=256):
        try:
            r = requests.get(url, stream=True)
            with open(save_path, 'wb') as fd:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    fd.write(chunk)
            return True
        except:
            print('Error. Could not download file:', url)
            return False

    def patchRomFile(self, sourcefile, patchfile, targetfile):
        sf = sourcefile.replace('\\', '/')
        tf = patchfile.replace('\\', '/')
        pf = targetfile.replace('\\', '/')
        # print('Source:', sf)
        # print('Patch:', tf)
        # print('Target:', pf)
        try:
            sf = open(sourcefile, 'rb')
            tf = open(targetfile, 'wb')
            pf = open(patchfile, 'rb')
            bps.apply.apply_to_files(pf, sf, tf)
            pf.close()
            tf.close()
            sf.close()
            print('Successfully patched the file...')
            return True
        except:
            print('Failed to patched the file...')
            return False

    def sendProgressBar(self, current, total):
        try:
            value = round((current/total)*100)
            self.update_progress.emit(value)
        except:
            pass

    def sendConsole(self, text):
        self.update_console.emit(text)

    def getCurrentDir(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return application_path


class WThreadGetMoreInfo(QtCore.QThread):
    snesRomInfoUrl = 'https://www.smwcentral.net/?p=section&a=details&id='
    currentDir = None
    update_progress = QtCore.pyqtSignal(int)
    update_console = QtCore.pyqtSignal(str)
    update_delete = QtCore.pyqtSignal(str)
    update_description = QtCore.pyqtSignal(dict)
    update_images = QtCore.pyqtSignal(list)
    romId = None
    currentOS = None

    def __init__(self, id):
        super(WThreadGetMoreInfo, self).__init__()
        self.currentDir = self.getCurrentDir()
        self.getOS()
        self.romId = id

    def run(self):
        # OPEN MORE INFO PAGE
        website = self.snesRomInfoUrl+str(self.romId)
        source = requests.get(website).text

        # CHECK IF POST HAS BEEN DELETED
        try:
            if 'File not found.<br>' in source:
                self.update_delete.emit(str(self.romId))
                return
        except:
            pass

            # GRAB DESCRIPTION
        try:
            resultDesc = source.split('Description:')[1].split('</tr>')[0]
            result = resultDesc.split('<td>')[1].split('</td>')[0].replace('<br>', '').strip()
            update = {
                'id': self.romId,
                'description': result
            }
            self.update_description.emit(update)
        except:
            print('Could not grab description from web. ID:', self.romId)

        # GRAB ALL IMAGES
        try:
            resultImagesText = source.split(
                '"slideshow", images: [')[1].split(']}];')[0]
            imgLinks = []
            pattern = re.compile("\/\/(.*?)'")
            for img in re.findall(pattern, resultImagesText):
                imgName = img.split(
                    'dl.smwcentral.net/image/')[1].split('.png')[0]
                f = {
                    'link': 'https://'+img,
                    'imgName': imgName+'.png'
                }
                imgLinks.append(f)

            # DOWNLOAD IMAGES
            savePath = self.currentDir+'/data/images/'+self.romId+'/'
            self.createFolder('images/'+self.romId)
            sendImg = []
            for img in imgLinks:
                self.downloadImage(img['link'], savePath+img['imgName'])
                path = savePath+img['imgName']
                send = {
                    'id': self.romId,
                    'image': path
                }
                sendImg.append(send)
            # SEND SUCCESS
            self.update_images.emit(sendImg)
        except:
            print('Could not grab images (thread)...')

    def getOS(self):
        curOS = platform.system()
        if curOS == 'Darwin':
            self.currentOS = 'MacOS'
        elif curOS == 'Linux':
            self.currentOS = 'Linux'
        elif curOS == 'Windows':
            self.currentOS = 'Windows'
        else:
            print('Could not get correct system.')
            return False
        print('Currently on:', self.currentOS)

    def createFolder(self, folder):
        # CREATE FOLDER
        try:
            if self.currentOS == 'Windows':
                os.makedirs(self.currentDir+'/data/'+folder, exist_ok=True)
            if self.currentOS == 'MacOS':
                os.makedirs(self.currentDir+'/data/'+folder)
            if self.currentOS == 'Linux':
                os.makedirs(self.currentDir+'/data/'+folder)
            print('Created folder: /data/'+folder)
            return True
        except OSError as err:
            print('Could not create folder: /data/'+folder,
                  'The folder maybe already exist...?')

    def downloadImage(self, url, save_path, chunk_size=256):
        r = requests.get(url, stream=True)
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)

    def getCurrentDir(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return application_path

####################
### UI FUNCTIONS ###
####################


class UIFunctions(MainWindow):
    def toggleMoreInformation(self, maxWidth, enable):
        if enable:

            # GET WIDTH
            width = self.ui.frame_more_info.width()
            maxExtend = maxWidth
            standard = 0

            # SET MAX WIDTH
            if width == 0:
                widthExtended = maxExtend
            else:
                widthExtended = standard

            # ANIMATION (MINIMUM)
            self.animation = QtCore.QPropertyAnimation(
                self.ui.frame_more_info, b"minimumWidth")
            self.animation.setDuration(400)
            self.animation.setStartValue(width)
            self.animation.setEndValue(widthExtended)
            self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
            self.animation.start()


######################
### LIST FUNCTIONS ###
######################
class AlignDelegate(QtWidgets.QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super(AlignDelegate, self).initStyleOption(option, index)
        option.displayAlignment = QtCore.Qt.AlignCenter


###############
### DIALOGS ###
###############
class helpDialog(QtWidgets.QDialog):
    currentDir = None

    def __init__(self, parent=None):
        super(helpDialog, self).__init__()
        self.ui = Ui_dialogAbout()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowSystemMenuHint |
                            QtCore.Qt.WindowTitleHint)
        self.currentDir = self.getCurrentDir()
        self.setFixedSize(self.size())
        self.setWindowTitle("About SMW: Simple Patcher")
        icon = QtGui.QIcon(':/img/icon.png')
        self.setWindowIcon(icon)

        self.ui.btnOk.clicked.connect(self.accept)

    def getCurrentDir(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        elif __file__:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return application_path


############
### MAIN ###
############
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    smwh = MainWindow()
    data = smwh.getAllHacks()
    smwh.loadDataToList(data)
    smwh.show()
    try:
        sys.exit(app.exec_())
    except:
        smwh.disconnect()
        print('Exiting')
