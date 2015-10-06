#!/usr/bin/env python
"""setupW32.py: A cw_freeze build wrapper."""

__author__  = "Minos Galanakis"
__license__ = "LGPL"
__version__ = "2.1"
__email__   = "minos197@gmail.com"

import os, site, sys
from cx_Freeze import setup, Executable

# Get the site-packages folder
site_dir = site.getsitepackages()[1]
include_dll_path = os.path.join(site_dir, "gnome")
print os.path.join(site_dir, "gnome")

# Required dll ( Installation specific )
missing_dll = ['libgtk-3-0.dll',
               'libgdk-3-0.dll',
               'libatk-1.0-0.dll',
               'libcairo-gobject-2.dll',
               'libgdk_pixbuf-2.0-0.dll',
               'libjpeg-8.dll',
               'libpango-1.0-0.dll',
               'libpangocairo-1.0-0.dll',
               'libpangoft2-1.0-0.dll',
               'libpangowin32-1.0-0.dll',
               'libharfbuzz-gobject-0.dll',
               'librsvg-2-2.dll',
               'libdbus-1-3.dll',
               'libdbus-glib-1-2.dll',
               'libffi-6.dll',
               'libfontconfig-1.dll',
               'libfreetype-6.dll',
               'libgailutil-3-0.dll',
               'libgio-2.0-0.dll',
               'libgirepository-1.0-1.dll',
               'libglib-2.0-0.dll',
               'libgmodule-2.0-0.dll',
               'libgobject-2.0-0.dll',
               'libgthread-2.0-0.dll',
               'libintl-8.dll',
               'libpng16-16.dll',
               'libwinpthread-1.dll',
               'libxmlxpat.dll',
               'libzzz.dll'
]

# Adding required the gtk libraries
gtk_libs = ['etc/gtk-3.0','etc/fonts','etc/pango', 'lib/girepository-1.0','share/glib-2.0']

# Create the list of includes
include_files = []
for dll in missing_dll:
    include_files.append((os.path.join(include_dll_path, dll), dll))

# Append the library files
for lib in gtk_libs:
    include_files.append((os.path.join(include_dll_path, lib), lib))

# Add the extra files
include_files.append("cdsk.glade")
include_files.append("ChromeDesk_Readme.pdf")
include_files.append("status.png")

# Set platform to disable the console
if sys.platform == "win32":
    base = "Win32GUI"
else:
    print "Incorrect system platform. Cx_Freeze will only work on Windows"
    sys.exit(0)

# Set the Executable
executables = [
    Executable("chromeGUI.py",
                base=base
    )
]

buildOptions = dict(
    compressed = False,
    includes = ["gi"],
    packages = ["gi"],
    include_files = include_files
    )

setup(
    name = "ChromeDesk",
    author = "Minos Galanakis",
    version = "0.3",
    description = "ChromeCast Wallpaper Rotator",
    options = dict(build_exe = buildOptions),
    executables = executables
)
