# ChromeDesk #

* Chromedesk is a chromecast wallpaper parsing class ,with optional CLI and GUI clients.
* Chromedesk connects to google chromecast image stream and rotates the desktop wallpaper acccordingly.
* The name of original author of each image is also retrieved and exposed to the filename.
* Version 0.3

### Requirements ###

* [Executable requires Microsoft Visual C++ 2008 SP1 Redistributable Package](http://www.microsoft.com/en-us/download/details.aspx?id=5582)
* Requires GI repository and GObject: `sudo apt-get install python-gi` or [PyGOBject AIO Windows](http://sourceforge.net/projects/pygobjectwin32/files)
* Pango, GDK Pixbuff not required but recommended in Windows ( Choose them in the installer )
* Build for python 2.7.xx
* [Includes setup script to build standalone executables](http://cx-freeze.sourceforge.net/)
* Comes with a user manual.

### How to include it in your own project ###

```
cd yourprojectdir
git submodule add https://github.com/minosg/chromedesk.git ./submodules
from submodules.chromeDesk import ChromeDesk
cd = ChromeDesk( period, download_dir )
```

 ChromeDesk can be then updated with:
`git submodule update --recursive`

### How to run as a python program ###

```
git clone https://github.com/minosg/chromedesk.git
cd chromedesk
git checkout gui
python chromeGUI
```

### How to compile as a windows standalone program ###

Follow the previous steps and instead of running freeze it using:
`python setupW32.py build --build-exe ChromeDesk`

_Note that the library files inluded in the setup file can vary depending on your
windows GTK3 aio installation._

### Not fully operational needs to get adjusted for the ChromeCast2 Stream ###
