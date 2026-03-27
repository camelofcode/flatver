import subprocess
import configparser
import os
from typing import List, Dict, Optional

class FlatpakManager:
    """Handles communication with the Flatpak CLI."""

    @staticmethod
    def _run_cmd(cmd: List[str]) -> subprocess.CompletedProcess:
        # We run without a tty to force machine-readable/tab-separated output where applicable
        return subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "PAGER": "cat"})

    @staticmethod
    def list_apps() -> List[Dict[str, str]]:
        """Returns a list of installed flatpaks with their details."""
        result = FlatpakManager._run_cmd(['flatpak', 'list', '--app', '--columns=application,name,version,branch,origin'])
        apps = []
        if result.returncode != 0:
            return apps
        
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
            parts = line.split('\t')
            # Fallback if flatpak didn't output tabs
            if len(parts) < 5:
                parts = [p for p in line.split(' ') if p]
                if len(parts) >= 5:
                    # Naively join name parts if there are spaces in the name, but flatpak list usually uses tabs when not a tty
                    app_id = parts[0]
                    origin = parts[-1]
                    branch = parts[-2]
                    version = parts[-3]
                    name = " ".join(parts[1:-3])
                    parts = [app_id, name, version, branch, origin]
                else:
                    parts = line.split('\t') + [""] * 5 # Fallback to prevent IndexError

            # Handle potentially missing parts if version is empty
            if len(parts) >= 5:
                # App ID usually at 0, name at 1, version at 2, branch at 3, origin at 4
                app_id, name, version, branch, origin = parts[:5]
                apps.append({
                    "app_id": app_id.strip(),
                    "name": name.strip(),
                    "version": version.strip(),
                    "branch": branch.strip(),
                    "origin": origin.strip()
                })
        return apps

    @staticmethod
    def get_app_commits(app_id: str, origin: str) -> List[Dict[str, str]]:
        """Returns the commit history for a specific app."""
        # Log includes: Commit, Subject, Date
        result = FlatpakManager._run_cmd(['flatpak', 'remote-info', '--log', origin, app_id])
        commits = []
        if result.returncode != 0:
            return commits
        
        current_commit = {}
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line:
                if current_commit:
                    commits.append(current_commit)
                    current_commit = {}
                continue
            
            if line.startswith('Commit:'):
                current_commit['commit'] = line.replace('Commit:', '').strip()
            elif line.startswith('Subject:'):
                current_commit['subject'] = line.replace('Subject:', '').strip()
            elif line.startswith('Date:'):
                current_commit['date'] = line.replace('Date:', '').strip()

        if current_commit:
            commits.append(current_commit)
            
        return commits

    @staticmethod
    def get_masked_apps() -> List[str]:
        """Returns a list of masked app IDs or patterns."""
        result = FlatpakManager._run_cmd(['flatpak', 'mask'])
        if result.returncode != 0:
            return []
        lines = result.stdout.strip().split('\n')
        masked = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('Pattern'):
                masked.append(line.split()[0]) # usually returns pattern as first column
        return masked

    @staticmethod
    def mask_app(app_id: str) -> bool:
        """Masks an app so it will not update."""
        cmd = ['flatpak', 'mask', app_id]
        result = FlatpakManager._run_cmd(cmd)
        return result.returncode == 0

    @staticmethod
    def unmask_app(app_id: str) -> bool:
        """Removes the mask on an app."""
        cmd = ['flatpak', 'mask', '--remove', app_id]
        result = FlatpakManager._run_cmd(cmd)
        return result.returncode == 0

    @staticmethod
    def is_system_app(app_id: str) -> bool:
        """Checks if the flatpak is installed system-wide."""
        result = FlatpakManager._run_cmd(['flatpak', 'info', app_id])
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip().startswith('Installation:') and 'system' in line:
                    return True
        return False

    @staticmethod
    def downgrade_app(app_id: str, commit: str) -> subprocess.CompletedProcess:
        """Downgrades an app to a specific commit. Note: This can take time."""
        cmd = ['flatpak', 'update', f'--commit={commit}', '-y', app_id]
        if FlatpakManager.is_system_app(app_id):
            cmd.insert(0, 'pkexec')
        # We might want this to run interactively or asynchronously in the GUI, but here we return the process result
        return FlatpakManager._run_cmd(cmd)

    @staticmethod
    def get_app_metadata(app_id: str) -> Dict[str, str]:
        """Fetches metadata to get homepage or github link if possible."""
        result = FlatpakManager._run_cmd(['flatpak', 'info', '--show-metadata', app_id])
        metadata = {}
        if result.returncode != 0:
            return metadata
        
        parser = configparser.ConfigParser()
        try:
            parser.read_string(result.stdout)
            if parser.has_section('Application'):
                for key, val in parser.items('Application'):
                    metadata[key] = val
        except Exception:
            pass
        return metadata

    @staticmethod
    def get_installed_commit(app_id: str) -> str:
        """Parses the installed commit hash from flatpak info."""
        result = FlatpakManager._run_cmd(['flatpak', 'info', app_id])
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip().startswith('Commit:'):
                    return line.split('Commit:')[1].strip()
        return ""

    @staticmethod
    def is_app_masked(app_id: str) -> bool:
        masked_patterns = FlatpakManager.get_masked_apps()
        return any(pattern == app_id or (pattern.endswith('*') and app_id.startswith(pattern[:-1])) for pattern in masked_patterns)
