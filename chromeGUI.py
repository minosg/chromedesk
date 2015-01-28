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
  from gi.repository import Gtk, Gdk, GObject, Pango
except ImportError as err:
  print "Error: %s"%s
  print "Please install pygi-aio"
  raw_input( "Press any key to exit" )
  sys.exit(0)


class ChromeGUI:

  #######################
  #    Initialization   #
  #######################

  def __init__( self ):
    '''Init the GUI object'''
    self.builder = Gtk.Builder()
    self.builder.add_from_file( "cdsk.glade" )
    self.builder.connect_signals(self)
    self.startup()
  
    self.window = self.builder.get_object( "main_window" )
    self.window.show_all()
    self.status = self.builder.get_object( "statusicon" )

  def startup( self ):
    '''Set the start-up default parameters'''
    download_dir = 'Wallpapers'
    period       = 10

    #set the chrome parser
    self.chromeparser = ChromeDesk( period,download_dir )
    self.chromeparser.set_image_picker( 'random' )
    directory = os.path.join(os.path.dirname( os.path.abspath( 'chromeGUI.py' ) ),download_dir )

    #GTK builder entry fields
    self.builder.get_object( "entry_rotation" ).set_text( str( period ) )
    self.builder.get_object( "checkbutton_autodel" ).set_active( False )
    self.builder.get_object( "checkbutton_tray" ).set_active( False)

    #if the directory does not exist make it
    if not os.path.exists(directory):
      os.makedirs(directory)
    self.builder.get_object( "filechooserbutton_download" ).set_filename( directory )

    #Control Variables
    self.run   = False
    self.pause = False


  #######################
  #         Signals     #
  #######################

  def on_filechooserbutton_download_file_set( self, selection ):
    ''' Called after a new download has been set '''
    #Reset any running session
    self.builder.get_object( "togglebutton_pause" ).set_active( False )
    self.builder.get_object( "togglebutton_run" ).set_active( False )
    #notify the chromeparser of the new selection
    self.chromeparser.set_download_dir( selection.get_filename() )

  def on_main_window_button_press_event (self, *args):
    ''' Called on mouse clicks over the app window '''
    dialog = self.builder.get_object( "aboutdialog_chrome" )
    #if right click then show dialog
    if args[1].button == 3:
      response = dialog.run()

      if response == Gtk.ResponseType.DELETE_EVENT:
        dialog.hide() 

  def on_button_runonce_pressed( self, button ):
    ''' Called from run once button '''
    if self.run == False:
      self.chromeparser.next()

  def on_popup_pause_toggled( self, button ):
    ''' Called from Pause button state change'''
    if button.get_active():
      button.set_label( "Resume" )
      self.pause = True
    else:
      button.set_label( "Pause" )
      self.pause = False

  def on_radiobutton_random_group_changed( self, button ):
    ''' Called from radio button cycle change'''
    if button.get_active():
      self.chromeparser.set_image_picker( "random" )
    else:
      self.chromeparser.set_image_picker( "incremental" )

  def on_checkbutton_autodel_toggled( self, button ):
    ''' Called on checkbox auto delete change '''
    if button.get_active():
      self.chromeparser.set_image_cleanup( True )
    else:
      self.chromeparser.set_image_cleanup( False )

  def on_togglebutton_run_toggled( self, button ):
    ''' Called on button run change '''
    if button.get_active():
      button.set_label( "Stop" )
      self.run = True
      GObject.idle_add(self.timer().next)
    else:
      button.set_label( "Run" )
      self.run = False

  def on_popup_run_activate( self, *args ):
    ''' Called pop-up run '''
    self.run = True

  def on_popup_quit_activate( self, *args ):
    ''' Called pop-up quit '''
    self.status.set_visible( False )
    Gtk.main_quit(*args)

  def on_statusicon_button_press_event( self, *args ):
    ''' Called popup pause '''
    #Left Click -> Maximize
    if args[1].button == 1:
      self.status.set_visible( False )
      self.builder.get_object( "checkbutton_tray" ).set_active( False )
      self.window.show_all()
    #right click
    elif args[1].button == 3:
      self.pup = self.builder.get_object( "status_popup")
      self.pup.popup( None,None, None, None,  args[1].button ,  args[1].time )

  def on_checkbutton_tray_toggled( self, button ):
    ''' Called when left clicking pop-up '''
    if button.get_active():
      self.status.set_visible( True )
    else:
      self.status.set_visible( False )

  def on_checkbutton_tray_leave_event(self,window,event):
    '''Called when the mouse cursor leaves the pop-up draw area'''
    if event.detail == Gdk.NotifyType.VIRTUAL:
      self.pup.hide()

  def on_main_window_delete_event( self, *args ):
    ''' Called when main window is destroyed by (x) button '''
    if self.builder.get_object( "checkbutton_tray" ).get_active():
      self.window.hide_on_delete()
      return True
    else:
      Gtk.main_quit(*args)


  #######################
  #    Generators       #
  #######################

  def timer( self ):
    ''' A generator timer implementation instead of a threaded one'''
    ref_time = time.time()
    timeout  = float(self.builder.get_object( "entry_rotation" ).get_text()) * 60.0
    iterations = 0.0
    while( self.run ):
      cur_time = time.time()

      #if pause is pressed wait
      if self.pause:
        self.status.set_tooltip_text("Paused")
        time.sleep(0.2)
        yield True
        continue

      #Else run and compare timers
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

      #put the program to sleep to preserve cpu cycles.
      time.sleep(0.05)
      yield True
    self.status.set_tooltip_text("Stopped")
    yield False


if __name__ == '__main__':
  #Create the object
  main = ChromeGUI()
  #run it
  Gtk.main()
  #When GTK loop ends quit app
  sys.exit()

