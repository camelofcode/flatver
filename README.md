# Flatver

![Flatver Screenshot](https://raw.githubusercontent.com/camelofcode/flatver/main/screenshot.png)

Flatver is a simple and elegant GUI application to manage your Flatpak versions, built with Python, GTK4, and Libadwaita.

With Flatver, you can easily:
- View all your installed Flatpaks and their version details
- See the full version/commit history for any installed app
- Downgrade applications to a specific previous version
- Mask applications to prevent unwanted auto-updates

## Building and Running

Flatver is built to be run as a Flatpak itself. You can build it locally using `flatpak-builder`:

```bash
# Build and install locally
flatpak-builder --user --install --force-clean build-dir com.github.camelofcode.Flatver.yml

# Run the app
flatpak run com.github.camelofcode.Flatver
```

## Flathub Submission
If you're building this for Flathub, use the `flathub-manifest.yml` instead, which pulls the source directly from this repository rather than using local files.

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later). See the [LICENSE](LICENSE) file for more details.

The AppStream metadata (`com.github.camelofcode.Flatver.metainfo.xml`) is licensed under CC0-1.0.
