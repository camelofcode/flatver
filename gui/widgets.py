import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Pango

class AppRow(Gtk.ListBoxRow):
    def __init__(self, app_data):
        super().__init__()
        self.app_data = app_data
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Flatpak icons usually match their app ID and are installed system-wide
        icon = Gtk.Image.new_from_icon_name(app_data['app_id'])
        icon.set_pixel_size(48)
        
        # Set a fallback icon if it doesn't exist. Actually, GTK handles missing named 
        # icons gracefully by showing an image-missing icon.
        box.append(icon)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_hexpand(True)
        
        name_label = Gtk.Label(label=app_data['name'])
        name_label.set_halign(Gtk.Align.START)
        name_label.set_ellipsize(Pango.EllipsizeMode.END)
        name_label.add_css_class('heading')
        vbox.append(name_label)
        
        id_label = Gtk.Label(label=app_data['app_id'])
        id_label.set_halign(Gtk.Align.START)
        id_label.add_css_class('dim-label')
        vbox.append(id_label)
        
        box.append(vbox)
        self.set_child(box)

class CommitRow(Adw.ActionRow):
    def __init__(self, commit_data, is_current=False):
        super().__init__()
        self.commit_data = commit_data
        
        date = commit_data.get('date', 'Unknown Date')
        subject = commit_data.get('subject', 'No Subject')
        commit_hash = commit_data.get('commit', '')
        
        self.set_title(f"{date} - {subject}")
        self.set_subtitle(f"Commit: {commit_hash[:8]}")
        
        if is_current:
            icon = Gtk.Image.new_from_icon_name("object-select-symbolic")
            self.add_prefix(icon)
            
        self.deploy_btn = Gtk.Button(label="Deploy")
        self.deploy_btn.set_valign(Gtk.Align.CENTER)
        self.deploy_btn.add_css_class("suggested-action")
        if is_current:
            self.deploy_btn.set_sensitive(False)
            self.deploy_btn.set_label("Current")
            self.deploy_btn.remove_css_class("suggested-action")
            
        self.add_suffix(self.deploy_btn)
