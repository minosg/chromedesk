#!/usr/bin/env python

"""html_utils.py: Utilities that parse the html block stream from Google ..."""

__author__  = "minos197@gmail.com"
__license__ = "LGPL"
__version__ = "3.0"
__email__   = "minos197@gmail.com"

import os
import glob
import unicodedata
import urllib2
import requests

def untitled_count(path):
    """ Return the biggest available index number for Unitled Images"""

    flist = glob.glob(os.path.join(path,"Unitled*"))
    max_no = 0
    for f in flist:
        #len("Untitled") = 8 + 3decima digits
        index = int(f[8:11])
        if index > max_no: max_no = index
    return max_no+1

def unicode_normalize(text):
    """Normalize unicode chars inheritted from url parsing"""

    text = urllib2.unquote(text)
    tmp_text = u""
    for char in text:
        tmp_text += unichr(ord(char))
    norm_text = unicodedata.normalize('NFKD', tmp_text).encode('ASCII', 'ignore')
    return norm_text

def get_image_bounds(text):
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

def entry_split(selection):
    """Split a section of text into a list ingoring commas between
    brackets."""

    # Trim the first set of brackets
    text_sel = selection[1:-1]

    # Locate next set of brackets
    idx_start, idx_end = get_image_bounds(text_sel)
    if idx_start + idx_end:
        output = text_sel[:idx_start].split(",") +\
            [text_sel[idx_start:idx_end]] +\
            text_sel[idx_end:].split(",")
    # If no brackets just split the datase
    else:
        output = text_sel.split(",")
    return output

def parse_entry(entry):
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
        # Sometimes attribution in entry includes subfolder ( remove it )
        output["author"] = entry[12].replace(" ", "_").replace("/", "_")
    else:
        output["author"] = entry[1].replace(" ", "_").replace("/", "_")
    
    # Remove trailling photo by
    output["author"] = output["author"].replace("Photo_by_", "")

    # Convert unicode chars 
    #TODO (Decide how converting the name causes copyright issue)
    # output["author"] =unicode_normalize(output["author"]

    output["host"] = entry[13]
    # Field 15 may contain usefull nested info. Parse and extract it
    if "null" not in entry[15]:
        details = extract_refs(entry[15])
        for key in details:
            output[key] = details[key]
    return output

def get_title(entry, dl_path):
    """ Retrieve the title of an image """

    # Set the title for the image
    if "title" in entry.keys() and "null" not in entry["title"]:
        title = entry["title"]
    elif "original_src" in entry.keys()and "null" not in entry["original_src"]:
        title = guess_name(entry["original_src"])
    elif "secondary_link" in entry.keys()and "null" not in entry["secondary_link"]:
        title = guess_name(entry["secondary_link"])
    # TODO: Add Debug line
    # TODO: Add More Elaborate proccessing for chromecast, satellites titles
    # TODO: Add incrementing untitled names
    else:
        utitled_cntr = 0
        title = "Untitled%.3d_"%untitled_count(dl_path)
    # Spaces in filenames will break image picker
    return title.replace(" ","_")

def extract_refs(field):
    """Extracts information from field 15 of the dataset."""

    text = field[1:-1]  # Remove trailling brackets
    st = nd = 0  # Start end pointers
    output = []  # Intermediate output container
    outdict = {}  # output array
    # Locate brackets inside the dataset.If locate fails it will return neg
    while st >= 0 or nd >= 0:
        st, nd = get_image_bounds(text)
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

def convert_gplus_to_name(link):
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
    return unicode_normalize(text)

def guess_name(link):
    """ Attempt to find the file name from the http-url"""

    # Google plus needs special resolution
    if "plus.google.com" in link:
        return convert_gplus_to_name(link)
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
    return unicode_normalize(name)

def get_page(url):
    """Open the address and return the data """

    try:
        return urllib2.urlopen(url).read()
    except urllib2.HTTPError:
        raise IOError


def get_source():
    """Read the raw ChromeCast html stream from Google."""

    text =  urllib2.urlopen(
        'https://clients3.google.com/cast/chromecast/home').read()

    # Images are packed as a json contained serialized object
    origin = text.find("JSON.parse")
    end_index = text.find(")). constant")
    text = text[origin + 14:end_index]

    # replace utf-8 '=' char with ASCII equivalent
    text = text.replace("\\u003d", "=")
    text = text.replace("\\u0026", "&")

    # remove redundant escape chars ( CleanUp )
    text = text.replace("\\", "")
    text = text.replace("x22", "")
    text = text.replace("\/", "/")

    return text

def image_downloader(change_cb, empty_cb, data, download_dir):
    ''' Threaded down-loader. When the first image is downloaded
     the downloaded will call the change wallpaper callback'''

    output = {}
    first_img = True
    # Check if download directory exits and make it if not
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    # Go through the links and download->save each of the files
    # TODO rewrite it to be more efficient and pretty
    selection = 0

    for entry in data:
        # Set the information for the image
        title = get_title(entry, download_dir)
        img_name = entry["main_link"]
        author = entry["author"]

        try:
            output[author] = urllib2.urlopen(img_name).read()

        except urllib2.HTTPError:
            print "Image not found in server", img_name
            continue

        # peak in the binary data for file descriptor
        ftype = ""
        if "JFIF" in output[author][:15]:
            ftype = 'jpg'
        elif "PNG" in output[author][:15]:
            ftype = 'png'

        # Compose the file name
        fname = ("%s_by_%s.%s")%(title,author,ftype)

        # Test if there are invalid characters in the name                
        if " " in fname or "/" in fname:
            print "Warning, Invalid char (%s) detected in fname:\n%s"\
                %((("/","space")[int(" " in fname)]), fname)
            continue
        # Append the directory path to it and write it to disk
        fname = os.path.join(download_dir, fname)
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


if __name__ == "__main__":
    pass
