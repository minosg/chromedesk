from cx_Freeze import setup, Executable
from gi.repository import Gtk,GObject,Pango
from chromeDesk import ChromeDesk

#filechooserbutton_download
#entry_rotation
#checkbutton_random
#checkbutton_autodel
#checkbutton_tray
#button_run
#button_stop
#button_runonce

class ChromeGUI:
  def on_window1_delete_event(self, *args):
      Gtk.main_quit(*args)
 
  def __init__(self):
    self.builder = Gtk.Builder()
    self.builder.add_from_file("cdsk.glade")
    self.builder.connect_signals(self)
    self.window = self.builder.get_object("main_window")
    self.window.show_all()

  def startup(self):
    self.builder.get_object("entry_rotation").set_text("600")
    self.builder.get_object("checkbutton_random").set_active(True)
    self.builder.get_object("checkbutton_autodel").set_active(False)
    self.builder.get_object("checkbutton_tray").set_active(False)


if __name__ == '__main__':
  main = ChromeGUI()
  Gtk.main()

