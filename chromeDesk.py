#!/usr/bin/env python

"""ChromeDesk.py: A simple chrome-cast desktop wallpaper parser that
    allows app to download set as wallpapers images casted by google ."""

__author__  = "Minos Galanakis"
__license__ = "LGPL"
__version__ = "3.0"
__email__   = "minos197@gmail.com"

import urllib2
import requests
import ctypes
import os
import random
import threading
import platform
from functools import partial
import sys
import simplejson as json
import unicodedata
down_counter = 0

class ChromeDesk():

    def __init__(self, t_rotation=300, dl_dir='Wallpapers'):
        # Set current path to where the file is located
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
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
            title = self.get_title(entry)
            textd += "%r: %r\n"%(author,title)
        with open(("img_links_%d.log"%down_counter),"w") as F:
            F.write(textd)
        F.close()
        down_counter += 1
        print "Logged_links"

    def get_source(self):
        """Read the raw ChromeCast html stream from Google."""

        return urllib2.urlopen(
            'https://clients3.google.com/cast/chromecast/home').read()


    def unicode_normalize(self, text):
        """Normalize unicode chars inheritted from url parsing"""

        text = urllib2.unquote(text)
        tmp_text = u""
        for char in text:
            tmp_text += unichr(ord(char))
        norm_text = unicodedata.normalize('NFKD', tmp_text).encode('ASCII', 'ignore')
        return norm_text


    def locate_bounds(self, text):
        """Identify in a block of html text a data entry and return its
        relative position to the main string."""

        MAX_RECURSION = 8  # Max No of nested bracket expected
        k = 0
        entry_start = text.find("[")
        for index in range(0, MAX_RECURSION):
            # Slice off the tralling chars before "]"
            idx = (text[entry_start:].find("]", k)) + 1
            # Set the current working slice
            text_sel = text[entry_start:][:idx]

            # Count the open and closed brackets in the working slice
            if text_sel.count("[") == text_sel.count("]"):
                entry_end = entry_start + idx
                break
            k = idx + 1
        return entry_start, entry_end

    def entry_split(self, selection):
        """Split a section of text into a list ingoring commas between
        brackets."""

        # Trim the first set of brackets
        text_sel = selection[1:-1]

        # Locate next set of brackets
        idx_start, idx_end = self.locate_bounds(text_sel)
        if idx_start + idx_end:
            output = text_sel[:idx_start].split(",") +\
                [text_sel[idx_start:idx_end]] +\
                text_sel[idx_end:].split(",")
        # If no brackets just split the datase
        else:
            output = text_sel.split(",")
        return output

    def get_title(self, entry):
        """ Retrieve the title of an image """

        # Set the title for the image
        if "title" in entry.keys() and "null" not in entry["title"]:
            title = entry["title"]
        elif "original_src" in entry.keys()and "null" not in entry["original_src"]:
            title = self.guess_name(entry["original_src"])
        elif "secondary_link" in entry.keys()and "null" not in entry["secondary_link"]:
            title = self.guess_name(entry["secondary_link"])
        # TODO: Add Debug line
        # TODO: Add More Elaborate proccessing for chromecast, satellites titles
        # TODO: Add incrementing untitled names
        else:
            title = "Untitled"
        return title

    def extract_refs(self, field):
        """Extracts information from field 15 of the dataset."""

        text = field[1:-1]  # Remove trailling brackets
        st = nd = 0  # Start end pointers
        output = []  # Intermediate output container
        outdict = {}  # output array
        # Locate brackets inside the dataset.If locate fails it will return neg
        while st >= 0 or nd >= 0:
            st, nd = self.locate_bounds(text)
            e = text[st + 1:nd - 1]
            if len(e):
                output.append(e)
            text = text[nd:]
        # The first and always present dataset is the http to the content
        # source
        outdict["original_src"] = output[0].split(",")[-1]

        # If it contains author title or search querry include them
        if len(output) == 2:
            split_pnt = output[1].find(",http")
            outdict["title"] = output[1][:split_pnt].replace(", ", "_")
            outdict["search"] = output[1][split_pnt + 1:]
        return outdict

    def convert_gplus_to_name(self, link):
        """Set the tags in the html that contain the image."""

        # They may change in a gplus update
        srch_str = "<meta property=\"og:image\" content=\""
        srch_end = "\" /><meta property=\"og:site_name\""
        text = requests.get(link).text
        text = text[text.find(srch_str) + len(srch_str):text.find(srch_end)]
        # Sometimes the extension is included, trim it if that is the case
        text = text[text.rfind("/") + 1:].split(".")[0]
        # TOOD write a proper filter
        # Replace html space to underscore
        return self.unicode_normalize(text)

    def guess_name(self, link):
        """ Attempt to find the file name from the http-url"""

        # Google plus needs special resolution
        if "plus.google.com" in link:
            return self.convert_gplus_to_name(link)
        data = link.split("/")
        name = ""
        hscore = 0
        key_items = ["-", "by", "-stock", "-rest"]
        for item in data:
            mscore = 0
            # count how many of the trigger words are contained in each section
            for ki in key_items:
                if ki in item:
                    mscore += 1
                # The one with the most matches is considered a title
                if mscore >= hscore:
                    name = item
                    hscore = mscore
        # Remove author attribution if included in the name
        name = name.split("-by-")[0]
        return self.unicode_normalize(name)

    def extract_fields(self, entry):
        """Populate a dictionary with all the usuable information from a data
        entry line."""

        output = {}
        # Extract the Links
        img_link = entry[0]

        # Change the request to ask for the 1080 version of the image
        img_link = img_link.replace("s1280", "s1920")
        img_link = img_link.replace("w1280", "w1920")
        img_link = img_link.replace("h720", "h1080")

        # Get the primary source (proxy) of the image's binary blob
        output["main_link"] = img_link

        # Refference link (direct)
        output["secondary_link"] = entry[9]

        # There are two fields that attribute the creator
        if "null" in entry[1] and "null" not in entry[12]:
            output["author"] = entry[12].replace(" ", "_")
        else:
            output["author"] = entry[1].replace(" ", "_")

        # Remove trailling photo by
        output["author"] = output["author"].replace("Photo_by_", "")

        # Convert unicode chars 
        #TODO (Decide how converting the name causes copyright issue)
        # output["author"] =unicode_normalize(output["author"]

        output["host"] = entry[13]
        # Field 15 may contain usefull nested info. Parse and extract it
        if "null" not in entry[15]:
            details = self.extract_refs(entry[15])
            for key in details:
                output[key] = details[key]
        return output

    def extract_img(self, text):
        """Process raw html data into a dictionary containing download links
        and authors, then download them."""

        output = {}
        temp = []

        # Pre proccessing html clean up
        origin = text.find("JSON.parse")
        end_index = text.find(")). constant")
        text = text[origin + 14:end_index]

        # replace utf-8 '=' char with ASCII equivalent
        text = text.replace("\\u003d", "=")
        text = text.replace("\\u0026", "&")

        # remove redundant escape chars
        text = text.replace("\\", "")
        text = text.replace("x22", "")
        text = text.replace("\/", "/")

        # Extract the data into a usuable dictionary
        entry_start = 0
        formatted_data = []
        offset = 0
        while len(text):
            entry_start, entry_end = self.locate_bounds(text[entry_start:])
            entry_start += offset
            entry_end += offset
            # End the loop if it contains not usuable text
            if "https" not in text[entry_start:entry_end]:
                break
            formatted_data.append(
                self.extract_fields(
                    self.entry_split(
                        text[
                            entry_start:entry_end])))

            entry_start = entry_end
            offset = entry_end

        # download the images
        self.download_img(formatted_data)
        self.image_links = formatted_data
        self.log_links(formatted_data)
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

    def download_img(self, img_dict_list):
        """Set up a new thread to download the images contained in the
        img_dict."""

        def remove_empty():
            self.folder_empty = False

        #/Start of thread
        def background_downloader(change_cb, empty_cb):
            ''' Threaded down-loader. When the first image is downloaded
             the downloaded will call the change wallpaper callback'''

            output = {}
            first_img = True
            # Check if download directory exits and make it if not
            if not os.path.exists(self.dl_dir):
                os.makedirs(self.dl_dir)
            # Go through the links and download->save each of the files
            # TODO rewrite it to be more efficient and pretty
            selection = 0

            for entry in img_dict_list:
                # Set the information for the image
                title = self.get_title(entry)
                img_name = entry["main_link"]
                author = entry["author"]

                #img_name = img_dict_list[author]
                try:
                    output[author] = urllib2.urlopen(img_name).read()

                except urllib2.HTTPError:
                    print "Image not found in server", img_name
                    continue

                # peak in the binary data for file descriptor
                ftype = ""
                if "JFIF" in output[author][:15]:
                    ftype = '.jpg'
                elif "PNG" in output[author][:15]:
                    ftype = '.png'

                # Compose the file name
                if title:
                    fname = title.lower().replace(" ", "_") + ftype
                else:
                    fname = "Untitled" + ftype

                try:
                    # Append author
                    idx = fname.index('.')
                except Exception as e:
                    print "Index Error (.) not Found", e, fname

                try:
                    fname = fname[:idx] + "_by_" + author + fname[idx:]
                except UnicodeDecodeError:
                    print "Unicode Error" ,repr(author),repr(fname)
                # replace chars to make the naming more readable
                fname = fname.replace(" ", "_")

                fname = os.path.join(self.dl_dir, fname)
                try:
                    with open(fname, 'wb') as f:
                        f.write(output[author])
                    f.close()
                except IOError as errno:
                    print "IO Error:", errno, len(repr(errno))
                    # IOERROR 36 means filename too long

                # call the callback once
                if first_img:
                    # change the wallpaper to the file just downloaded
                    (lambda: change_cb(fname))()
                    # Notify the system the folder is no longer empty
                    empty_cb()
                    first_img = False
            #/End of thread

        # covert to a thread and start it
        thread = threading.Thread(
            target=background_downloader,
            args=(
                self.change,
                remove_empty,
            ))
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
        '''Assert the image clean-up flag to auto-delete images after being used '''

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
            #self.image_links = self.extract_img( self.get_source() )

    def image_picker(self):
        """Function that determines the next image to be set based on mode."""

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
            self.image_links = self.extract_img(self.get_source())
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
                SPI_SETDESKWALLPAPER,
                0,
                rimage,
                0)
        elif self.platform[0] == "Linux":
            window_manager = self.platform[1]
            rimage = os.path.abspath(rimage)
            if 'gnome' in window_manager:
                command = 'gconftool-2 -t string -s\
                    /desktop/gnome/background/picture_filename %s' % rimage
            elif 'kde' in window_manager:
                command = 'dcop kdesktop KBackgroundIface\
                   setWallpaper %s 1' % rimage
            elif "ubuntu" in window_manager:
                command = "gsettings set org.gnome.desktop.background\
                    picture-uri file:///%s" % rimage
            elif "mate" in window_manager:
                command = "gsettings set org.mate.background\
                    picture-filename %s" % rimage
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
