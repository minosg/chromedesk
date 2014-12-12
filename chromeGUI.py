from cx_Freeze import setup, Executable
from gi.repository import Gtk,GObject,Pango
from chromeDesk import ChromeDesk
import os,sys

#filechooserbutton_download
#entry_rotation
#checkbutton_random
#checkbutton_autodel
#checkbutton_tray
#button_run
#button_stop
#button_runonce
import time
class ChromeGUI:

  #######################
  #         Signals     #
  #######################
  def on_button_run_pressed( self, button ):
    self.run = True

  def on_button_runonce_pressed( self, button ):
    pass

  def on_button_stop_pressed( self, button ):
    self.run = True

  def on_popup_pause_activate( self, *args ):
    self.run = True

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
        #self.status.set_tooltip_text("Running in background")
      else:
        Gtk.main_quit(*args)

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
    #GTK builder entry fields
    self.builder.get_object("entry_rotation").set_text("600")
    self.builder.get_object("checkbutton_random").set_active(True)
    self.builder.get_object("checkbutton_autodel").set_active(False)
    self.builder.get_object("checkbutton_tray").set_active(False)

    directory = os.path.join(os.path.dirname(os.path.abspath('chromeGUI.py')),'Wallpapers')
    self.builder.get_object('filechooserbutton_download').set_filename(directory)

    #Control Variables
    self.run = False


if __name__ == '__main__':
  main = ChromeGUI()
  Gtk.main()
  sys.exit()

