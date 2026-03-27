import gi
import threading
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib
from core.manager import FlatpakManager
from gui.widgets import AppRow, CommitRow

class MainWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_default_size(1000, 700)
        self.set_title("Flatpak Manager")
        
        self.split_view = Adw.NavigationSplitView()
        self.set_content(self.split_view)
        # We need this to allow split view to show sidebar next to content on wide screens
        
        # Setup Sidebar
        self.app_listbox = Gtk.ListBox()
        self.app_listbox.add_css_class("navigation-sidebar")
        self.app_listbox.connect("row-activated", self.on_app_selected)
        
        sidebar_scroll = Gtk.ScrolledWindow()
        # Prevent the sidebar from scrolling right when focused
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_child(self.app_listbox)
        sidebar_scroll.set_vexpand(True)
        
        sidebar_toolbar = Adw.ToolbarView()
        header = Adw.HeaderBar()
        sidebar_toolbar.add_top_bar(header)
        sidebar_toolbar.set_content(sidebar_scroll)
        
        self.sidebar_page = Adw.NavigationPage.new(sidebar_toolbar, "sidebar")
        self.sidebar_page.set_title("Applications")
        self.split_view.set_sidebar(self.sidebar_page)
        
        # Setup Content
        self.content_toolbar = Adw.ToolbarView()
        self.content_header = Adw.HeaderBar()
        self.content_toolbar.add_top_bar(self.content_header)
        
        # Preferences Page for nice Flatseal-like UI
        self.pref_page = Adw.PreferencesPage()
        
        self.info_group = Adw.PreferencesGroup()
        self.info_group.set_title("Application Details")
        
        self.version_row = Adw.ActionRow()
        self.version_row.set_title("Current Version")
        self.info_group.add(self.version_row)
        
        self.branch_row = Adw.ActionRow()
        self.branch_row.set_title("Branch")
        self.info_group.add(self.branch_row)

        self.origin_row = Adw.ActionRow()
        self.origin_row.set_title("Origin (Remote)")
        self.info_group.add(self.origin_row)
        
        self.link_row = Adw.ActionRow()
        self.link_row.set_title("Links")
        self.info_group.add(self.link_row)
        
        self.pref_page.add(self.info_group)
        
        self.actions_group = Adw.PreferencesGroup()
        self.actions_group.set_title("Advanced Actions")
        
        self.mask_row = Adw.ActionRow()
        self.mask_row.set_title("Mask App")
        self.mask_row.set_subtitle("Prevent this application from auto-updating.")
        self.mask_switch = Gtk.Switch()
        self.mask_switch.set_valign(Gtk.Align.CENTER)
        self.mask_switch.connect("state-set", self.on_mask_toggled)
        self.mask_row.add_suffix(self.mask_switch)
        self.actions_group.add(self.mask_row)
        
        self.pref_page.add(self.actions_group)
        
        self.commits_group = Adw.PreferencesGroup()
        self.commits_group.set_title("Version History")
        self.commits_group.set_description("Loading commits...")
        self.pref_page.add(self.commits_group)
        self.commit_rows = []
        
        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_child(self.pref_page)
        self.content_toolbar.set_content(content_scroll)
        
        self.content_page = Adw.NavigationPage.new(self.content_toolbar, "content")
        self.content_page.set_title("Details")
        self.split_view.set_content(self.content_page)
        
        # Load data
        self.show_empty_state()
        self.load_apps()

    def show_empty_state(self):
        self.content_header.set_show_title(False)
        self.pref_page.set_visible(False)
        
        # Could add an AdwStatusPage here for empty state

    def load_apps(self):
        def fetch():
            apps = FlatpakManager.list_apps()
            # Sort apps alphabetically by name
            apps.sort(key=lambda x: x.get('name', '').lower())
            masked = FlatpakManager.get_masked_apps()
            GLib.idle_add(self.populate_sidebar, apps, masked)
        threading.Thread(target=fetch, daemon=True).start()

    def populate_sidebar(self, apps, masked):
        self.masked_patterns = masked
        for app in apps:
            row = AppRow(app)
            self.app_listbox.append(row)

    def on_app_selected(self, listbox, row):
        if not row:
            return
        
        app_data = row.app_data
        self.current_app = app_data
        self.content_header.set_show_title(True)
        self.content_header.set_title_widget(Adw.WindowTitle(title=app_data['name'], subtitle=app_data['app_id']))
        self.pref_page.set_visible(True)
        
        self.version_row.set_subtitle(app_data.get('version', 'Unknown'))
        self.branch_row.set_subtitle(app_data.get('branch', 'Unknown'))
        self.origin_row.set_subtitle(app_data.get('origin', 'Unknown'))
        
        # Check if masked
        app_id = app_data['app_id']
        is_masked = any(p == app_id or (p.endswith('*') and app_id.startswith(p[:-1])) for p in self.masked_patterns)
        
        # Temporarily block signal to avoid triggering the toggle action when loading
        self.updating_ui = True
        self.mask_switch.set_active(is_masked)
        self.updating_ui = False
        
        self.commits_group.set_description("Loading version history...")
        
        # Clear previous commits
        for row in getattr(self, 'commit_rows', []):
            try:
                self.commits_group.remove(row)
            except Exception:
                pass
        self.commit_rows = []
            
        # Fetch detailed info and commits in background
        def fetch_details():
            metadata = FlatpakManager.get_app_metadata(app_id)
            commits = FlatpakManager.get_app_commits(app_id, app_data['origin'])
            installed_commit = FlatpakManager.get_installed_commit(app_id)
            GLib.idle_add(self.update_app_details, metadata, commits, installed_commit)
            
        threading.Thread(target=fetch_details, daemon=True).start()
        
    def update_app_details(self, metadata, commits, installed_commit):
        # Update Links
        self.link_row.set_visible(False)
            
        if getattr(self, 'custom_link_box', None) is not None:
            try:
                self.link_row.remove(self.custom_link_box)
            except Exception:
                pass
            
        self.custom_link_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        homepage = metadata.get('url/homepage')
        if not homepage:
            homepage = metadata.get('url/bugtracker')
            
        if homepage:
            btn = Gtk.LinkButton(uri=homepage, label="Homepage")
            btn.set_valign(Gtk.Align.CENTER)
            self.custom_link_box.append(btn)
            self.link_row.set_visible(True)
            
        # If it's from Flathub, dynamically add the Flathub GitHub component link
        app_id = self.current_app['app_id']
        if self.current_app.get('origin') == 'flathub':
            gh_url = f"https://github.com/flathub/{app_id}"
            gh_btn = Gtk.LinkButton(uri=gh_url, label="GitHub Repo")
            gh_btn.set_valign(Gtk.Align.CENTER)
            self.custom_link_box.append(gh_btn)
            self.link_row.set_visible(True)
            
        self.link_row.add_suffix(self.custom_link_box)
            
        self.commits_group.set_description(f"Found {len(commits)} commits (Most recent first)")
        
        for i, commit in enumerate(commits):
            _hash = commit.get('commit', '')
            is_current = bool(installed_commit and _hash == installed_commit)
            row = CommitRow(commit, is_current=is_current)
            row.deploy_btn.connect("clicked", self.on_deploy_clicked, commit)
            self.commits_group.add(row)
            self.commit_rows.append(row)

    def on_mask_toggled(self, switch, state):
        if getattr(self, 'updating_ui', False):
            return False
            
        app_id = self.current_app['app_id']
        def toggle_mask():
            if state:
                success = FlatpakManager.mask_app(app_id)
            else:
                success = FlatpakManager.unmask_app(app_id)
            
            # Refresh masked patterns
            self.masked_patterns = FlatpakManager.get_masked_apps()
            
            def notify_done():
                pass # Can show a toast notification here
            GLib.idle_add(notify_done)
            
        threading.Thread(target=toggle_mask, daemon=True).start()
        return False # Accept state change

    def on_deploy_clicked(self, btn, commit):
        app_id = self.current_app['app_id']
        commit_hash = commit['commit']
        
        btn.set_sensitive(False)
        btn.set_label("Deploying...")
        
        def deploy():
            result = FlatpakManager.downgrade_app(app_id, commit_hash)
            def done():
                if result.returncode == 0:
                    btn.set_label("Deployed")
                    # Refresh the details view to show the new deployed commit
                    row = self.app_listbox.get_selected_row()
                    if row:
                        self.on_app_selected(self.app_listbox, row)
                else:
                    btn.set_sensitive(True)
                    btn.set_label("Failed")
                    print(result.stdout, result.stderr)
            GLib.idle_add(done)
            
        threading.Thread(target=deploy, daemon=True).start()
