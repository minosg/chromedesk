#!/usr/bin/env python

"""ChromeDesk.py: A simple chrome-cast desktop wallpaper parser that
    allows app to download set as wallpapers images casted by google ."""

__author__  = "Minos Galanakis"
__license__ = "LGPL"
__version__ = "3.0"
__email__   = "minos197@gmail.com"

import os
import sys
import ctypes
import random
import platform
import threading
import simplejson as json
from html_utils import *
down_counter = 0


class ChromeDesk():

    def __init__(self, t_rotation=300, dl_dir='Wallpapers'):

        # Set current path to where the file is located
        if getattr(sys, 'frozen', False):
            currnt_dir = os.path.dirname(sys.executable)
        else:
            currnt_dir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(currnt_dir)

        # Init Internal variables
        self.dl_dir = dl_dir
        self.t_rotation = t_rotation
        self.image_links = None
        self.folder_empty = True
        self.running = False
        self.imgp = 0
        self.choice = ""
        self.cleanup_flg = False
        self.platform = (platform.system(), os.getenv("DESKTOP_SESSION"))

    def log_links(self, data):
        """ Function that exports parsed content in a csv file """

        global down_counter
        textd = ""
        for entry in data:
            author = entry["author"]

            # Set the title for the image
            title = get_title(entry, self.gl_dir)
            textd += "%r: %r\n"%(author,title)
        with open(("img_links_%d.log"%down_counter),"w") as F:
            F.write(textd)
        F.close()
        down_counter += 1
        print "Logged_links"


    def get_images(self):
        """ Allows the application to trigger an update the image dataset """

        # Refresh page and get new links
        self.image_links = self.get_images_mdata()
        # Download the images
        self.download_images(self.image_links)

    def get_images_mdata(self):
        """Process raw html data into a dictionary containing download links
        and authors, then download them."""

        output = {}
        temp = []

        # Get the filtered chromecast homepage source
        text = get_source()

        # Extract the data into a usuable dictionary
        entry_start = 0
        formatted_data = []
        offset = 0
        while len(text):
            # Locate the start and end of next entry with meaningfull data
            entry_start, entry_end = get_image_bounds(text[entry_start:])
            entry_start += offset
            entry_end += offset
            # End the loop if it contains not usuable text
            if "https" not in text[entry_start:entry_end]:
                break
            # Get a slice of the working text, and proccess it into a csv list
            text_slice = entry_split(text[entry_start:entry_end])
            # Parse the entries of the list into a dictionary
            formatted_data.append(parse_entry(text_slice))

            # Shift the pointers for next iteration
            entry_start = entry_end
            offset = entry_end

        # self.log_links(formatted_data)      
        return formatted_data

    def stop_periodic_callback(self):
        """Sets the thread termination flag."""

        global t1_run_flag
        t1_run_flag = False

    def attach_periodic_callback(self, cb):
        """Add a periodic timer that when expires executes callback
        function."""

        global t1_run_flag

        # set the configuration
        t1_run_flag = True

        # Add background processes
        def background_timer(t_cycle, callback):
            import time
            global t1_run_flag

            ref_time = time.time()
            while (t1_run_flag):
                cur_time = time.time()
                if cur_time - ref_time >= t_cycle:
                    ref_time = cur_time
                    callback()
                if not t1_run_flag:
                    return
                time.sleep(0.5)
        # covert to a thread and start it
        thread = threading.Thread(
            target=background_timer,
            args=(
                self.t_rotation,
                cb,
            ))
        thread.daemon = True
        thread.start()

    def download_images(self, img_dict_list):
        """Set up a new thread to download the images contained in the
        img_dict."""

        def remove_empty():
            self.folder_empty = False

        # covert to a thread and start it
        thread = threading.Thread(target=image_downloader,\
            args=( self.change, remove_empty, img_dict_list, self.dl_dir,))
        thread.daemon = True
        thread.start()

    def set_download_dir(self, dir):
        """Create a directory to download images if it does not exist."""

        self.dl_dir = dir
        # Check if download directory exits and make it if not
        if not os.path.exists(self.dl_dir):
            os.makedirs(self.dl_dir)

        # reset the links database to force the program to dl them in new
        # location
        self.image_links = ''

    def set_image_cleanup(self, mode):
        """ Assert the image clean-up flag to auto-delete images after use """

        self.cleanup_flg = mode

    def set_image_picker(self, mode):
        """Set the image rotation mode."""
        sup_modes = {'random': 0, 'incremental': 1}
        if mode in sup_modes.keys():
            self.imgp = sup_modes[mode]

    def cleanup(self, filename):
        """Delete an image after it switched out of rotation."""

        if self.cleanup_flg:
            file = os.path.join(self.dl_dir, filename)
            os.remove(file)

        # if no images left in directory download new ones
        if not os.listdir(self.dl_dir):
            self.folder_empty = True
            self.get_images()

    def image_picker(self):
        """ Function that determines the next image to be set based on mode. """

        old_file = ''
        # keep a copy of the current filename
        if self.choice:
            old_file = self.choice

        # Get a list of the files in wallpaper directory
        wallpapers = os.listdir(self.dl_dir)
        if self.imgp == 0:
            # Select one at random
            while True:
                self.choice = random.choice(wallpapers)
                # make sure the same file is not chosen unless its is the only
                # one
                if self.choice not in old_file or len(wallpapers) == 1:
                    break

        elif self.imgp == 1:
            try:
                self.choice = wallpapers[wallpapers.index(self.choice) + 1]
            # If the first time it runs or index overflow
            except (IndexError, ValueError):
                self.choice = wallpapers[0]
        # Compose the path
        if old_file and self.choice:
            self.cleanup(old_file)
        return os.path.join(self.dl_dir, self.choice)

    def next(self):
        """Set the next image as wallpaper."""

        # If the images have not been downloaded yet
        if (self.folder_empty):
            self.get_images()
            self.choice = ''
            return
        # Select the next image file
        rimage = self.image_picker()
        self.change(rimage)

    def change(self, rimage):
        """Change the wallpaper to rimage based on the host desktop OS and
        environment."""

        command = ''

        # Change wallpaper based on host platform
        if self.platform[0] == "Windows":
            SPI_SETDESKWALLPAPER = 20

            # Set it as wallpaper
            ctypes.windll.user32.SystemParametersInfoA(
                SPI_SETDESKWALLPAPER, 0, rimage, 0)

        elif self.platform[0] == "Linux":
            window_manager = self.platform[1]
            rimage = os.path.abspath(rimage)
            if 'gnome' in window_manager:
                command = 'gconftool-2 -t string -s\
                    /desktop/gnome/background/picture_filename \"%s\"' % rimage
            elif 'kde' in window_manager:
                command = 'dcop kdesktop KBackgroundIface setWallpaper\
                    \"%s\" 1' % rimage
            elif "ubuntu" in window_manager:
                command = "gsettings set org.gnome.desktop.background\
                    picture-uri file:///%s" % rimage
            elif "mate" in window_manager:
                command = "gsettings set org.mate.background\
                    picture-filename \"%s\"" % rimage
            else:
                print "Unrecognised Desktop Environment %s" % window_manager
            os.system(command)
        else:
            print "Unrecognised platform %s" % self.platform[0]


if __name__ == '__main__':
    # Main code example
    cd = ChromeDesk()

    # Change the wallpaper once
    # cd.next()

    # Change the wallpaper with default rotation period ( 10 minutes )
    cd.attach_periodic_callback(cd.next)

    # Keep the program alive
    print ("Press CTRL+C to exit")
    while(True):
        pass
