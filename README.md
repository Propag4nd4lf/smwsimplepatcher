# SMW Simple Patcher

With this tool you will be able to download and patch Super Mario World roms really easy and fast.


## How to Install?

Get SMW Simple Patcher by downloading [the latest release](https://github.com/Propag4nd4lf/smwsimplepatcher/releases). It's currently only supported on Windows, but the source code should work on both MacOS and Linux __(but I have not tested it yet!)__.


## How do I use the program?

```
1  - Update the database.
2. - Download the essential files.
3. - Set an output folder.
4a - Select the hack and press "Download And Patch ROM".
4b - You can alternatively select multiple hacks to download/patch them all at once if you need to.
```

![](https://i.imgur.com/ZZNoXKC.gif)


## Python

If you are planning to run it from the source, you'll need to install a couple of packages.
```
pip install beautifulsoup4
pip install py7zr
pip install python-bps-continued
pip install PyQt5
pip install requests
```
Only been tested on Python version 3.8.10.


## Notes

- The Original Rom is _not_ located on Github or my server (__!__). The software simply just downloads it from an public website.
- If an hack no longer exists (this could happen if it was put out as an demo, and then removed), the download will fail. To remove it from the list, select the hack and press the button with the arrows circling around.
- If an hack has an zip file included in the original zip file, the patch will fail. You will need to manually patch that one.


## Licence

Do whatever you want with it. I was only making it to learn the Qt framework.
