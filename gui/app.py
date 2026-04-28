import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw
from gui.window import MainWindow

class FlatpakManagerApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.github.camelofcode.Flatver')

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self)
        win.present()
