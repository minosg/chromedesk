from cx_Freeze import setup, Executable
from gi.repository import Gtk, GObject, Pango
from chromeDesk import ChromeDesk
import os,sys,time

class ChromeGUI:

  #######################
  #         Signals     #
  #######################
  def on_button_run_pressed( self, button ):
    if self.run == False:
      self.run = True
      GObject.idle_add(self.timer().next)

  def on_button_runonce_pressed( self, button ):
    if self.run == False:
      self.chromeparser.change()

  def on_button_stop_pressed( self, button ):
    self.run = False

  def on_popup_pause_toggled( self, button ):
    if button.get_active():
      self.pause = True
    else:
      self.pause = False

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
    timeout  = float(self.builder.get_object("entry_rotation").get_text())
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
        self.chromeparser.change()
        iterations += 1.0

      #re-download the images after a  full cycle
      if iterations > timeout:
        print "Downloading images",iterations,timeout
        #self.chromeparser.extract_img(  self.chromeparser.get_source() )
        iterations = 0.0

      time.sleep(0.2)
      yield True
    self.status.set_tooltip_text("Stopped")
    yield False

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
    period       = 600

    #GTK builder entry fields
    self.builder.get_object("entry_rotation").set_text(str(period))
    self.builder.get_object("checkbutton_random").set_active(True)
    self.builder.get_object("checkbutton_autodel").set_active(False)
    self.builder.get_object("checkbutton_tray").set_active(False)

    #set the chrome parser
    self.chromeparser = ChromeDesk( period,download_dir )
    directory = os.path.join(os.path.dirname(os.path.abspath('chromeGUI.py')),download_dir)
    
    #if the directory does not exist make it
    if not os.path.exists(directory):
      os.makedirs(directory)
    self.builder.get_object('filechooserbutton_download').set_filename(directory)

    #Control Variables
    self.run   = False
    self.pause = False


if __name__ == '__main__':
  main = ChromeGUI()
  Gtk.main()
  sys.exit()

