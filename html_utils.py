#!/usr/bin/env python

"""html_utils.py: Utilities that parse the html block stream from Google ..."""

__author__  = "minos197@gmail.com"
__license__ = "LGPL"
__version__ = "3.0"
__email__   = "minos197@gmail.com"

import unicodedata
import urllib2
import requests

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


def get_title(entry):
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
        title = "Untitled"
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

    return urllib2.urlopen(
        'https://clients3.google.com/cast/chromecast/home').read()

if __name__ == "__main__":
    pass
