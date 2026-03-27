import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gui.app import FlatpakManagerApp

if __name__ == '__main__':
    app = FlatpakManagerApp()
    sys.exit(app.run(sys.argv))
