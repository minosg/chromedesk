#!/usr/bin/env python

"""ChromeGUI.py: A simple GTK3 interface for ChromeDesk class."""

__author__  = "Minos Galanakis"
__license__ = "LGPL"
__version__ = "2.1"
__email__   = "minos197@gmail.com"

#import standard libs
import os
import sys
import time

#import Chromedesk
from chromeDesk import ChromeDesk

#Attempt to import GTK3 libs
try:
  from gi.repository import Gtk, GObject, Pango
except ImportError as err:
  print "Error: %s"%s
  print "Please install pygi-aio"
  raw_input("Press any key to exit")
  sys.exit(0)


class ChromeGUI:

  #######################
  #    Initialization   #
  #######################

  def __init__( self ):
    self.builder = Gtk.Builder()
    self.builder.add_from_file("cdsk.glade")
    self.builder.connect_signals(self)
    self.startup()
  
    self.window = self.builder.get_object("main_window")
    self.window.show_all()
    self.status = self.builder.get_object("statusicon")

  def startup( self ):
    #defaults
    download_dir = 'Wallpapers'
    period       = 10

    #set the chrome parser
    self.chromeparser = ChromeDesk( period,download_dir )
    self.chromeparser.set_image_picker('random')
    directory = os.path.join(os.path.dirname(os.path.abspath('chromeGUI.py')),download_dir)

    #GTK builder entry fields
    self.builder.get_object("entry_rotation").set_text(str(period))
    self.builder.get_object("checkbutton_autodel").set_active(False)
    self.builder.get_object("checkbutton_tray").set_active(False)

    #if the directory does not exist make it
    if not os.path.exists(directory):
      os.makedirs(directory)
    self.builder.get_object('filechooserbutton_download').set_filename(directory)

    #Control Variables
    self.run   = False
    self.pause = False


  #######################
  #         Signals     #
  #######################

  def on_filechooserbutton_download_file_set(self, selection):
    #Reset any running session
    self.builder.get_object("togglebutton_pause").set_active(False)
    self.builder.get_object("togglebutton_run").set_active(False)
    #notify the chromeparser of the new selection
    self.chromeparser.set_download_dir( selection.get_filename() )

  def on_main_window_button_press_event (self, *args):
    dialog = self.builder.get_object("aboutdialog_chrome")
    #if right click then show dialog
    if args[1].button == 3:
      response = dialog.run()

      if response == Gtk.ResponseType.DELETE_EVENT:
        dialog.hide() 

  def on_button_runonce_pressed( self, button ):
    if self.run == False:
      self.chromeparser.next()

  def on_popup_pause_toggled( self, button ):
    if button.get_active():
      button.set_label("Resume")
      self.pause = True
    else:
      button.set_label("Pause")
      self.pause = False

  def on_radiobutton_random_group_changed( self, button ):
    if button.get_active():
      self.chromeparser.set_image_picker('random')
    else:
      self.chromeparser.set_image_picker('incremental')

  def on_checkbutton_autodel_toggled( self, button ):
    if button.get_active():
      self.chromeparser.set_image_cleanup( True )
    else:
      self.chromeparser.set_image_cleanup( False )

  def on_togglebutton_run_toggled( self, button ):
    if button.get_active():
      button.set_label("Stop")
      self.run = True
      GObject.idle_add(self.timer().next)
    else:
      button.set_label("Run")
      self.run = False

  def on_popup_run_activate( self, *args ):
    self.run = True

  def on_popup_quit_activate( self, *args ):
    self.status.set_visible( False )
    Gtk.main_quit(*args)

  def on_statusicon_button_press_event( self, *args ):
    #Left Click -> Maximize
    if args[1].button == 1:
      self.status.set_visible( False )
      self.builder.get_object("checkbutton_tray").set_active( False )
      self.window.show_all()
    #right click
    elif args[1].button == 3:
      pup = self.builder.get_object("status_popup")
      pup.popup( None,None, None, None,  args[1].button ,  args[1].time )

  def on_checkbutton_tray_toggled( self, button ):
    if button.get_active():
      self.status.set_visible( True )
    else:
      self.status.set_visible( False )

  def on_main_window_delete_event( self, *args ):
      if self.builder.get_object("checkbutton_tray").get_active():
        self.window.hide_on_delete()
        return True
      else:
        Gtk.main_quit(*args)


  #######################
  #    Generators       #
  #######################

  def timer( self ):
    ref_time = time.time()
    timeout  = float(self.builder.get_object("entry_rotation").get_text()) * 60.0
    iterations = 0.0
    while( self.run ):
      cur_time = time.time()

      #if pause is pressed wait
      if self.pause:
        self.status.set_tooltip_text("Paused")
        time.sleep(0.2)
        yield True
        continue

      self.status.set_tooltip_text("Running")
      if cur_time - ref_time >= timeout:
        ref_time = cur_time
        self.chromeparser.next()
        iterations += 1.0

      #re-download the images after a  full cycle
      if iterations > timeout:
        print "Downloading new images"
        self.chromeparser.extract_img(  self.chromeparser.get_source() )
        iterations = 0.0

      time.sleep(0.05)
      yield True
    self.status.set_tooltip_text("Stopped")
    yield False


  #######################
  #  Utility Functions  #
  #######################

  def delete_buffer(self, buffer):
    #get buffer end and start
    start = self.builder.get_object(buffer).get_buffer().get_start_iter()
    end = self.builder.get_object(buffer).get_buffer().get_end_iter()
    #detele the text between them
    self.builder.get_object(buffer).get_buffer().delete(start,end)

if __name__ == '__main__':
  main = ChromeGUI()
  Gtk.main()
  sys.exit()

