import subprocess


class ProcessManager:
    def __init__(self, logger):
        self.logger = logger

    def run(self, command: str) -> str:
        """Eksekusi perintah internal dengan hak akses superuser root."""
        try:
            root_command = f"su -c '{command}'"
            result = subprocess.run(root_command, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode != 0 or result.stderr.strip():
                self.logger.error(
                    f"Root command non-zero exit [{command}] rc={result.returncode} stderr={result.stderr.strip()}"
                )
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Root Execution failed: {e}")
            return ""

    def run_plain(self, command: str, timeout: int = 10) -> str:
        """Eksekusi perintah shell biasa tanpa root untuk modul non-launcher."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Shell execution failed [{command}]: {e}")
            return ""

    def force_stop(self, pkg: str) -> str:
        return self.run(f"am force-stop {pkg}")

    def launch_package(self, pkg: str, place_id: str = None) -> str:
        if place_id:
            cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {pkg} --activity-brought-to-front"
        else:
            main_act = self.resolve_activity(pkg)
            if main_act and "/" in main_act:
                cmd = f"am start -n {main_act} --activity-brought-to-front"
            else:
                cmd = f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"

        return self.run(cmd)

    def resolve_activity(self, pkg: str) -> str:
        return self.run(f"cmd package resolve-activity --brief {pkg} | tail -n 1")

    def is_running(self, pkg: str) -> bool:
        """Memeriksa apakah proses Android package aktif menggunakan perintah pidof."""
        pid = self.run(f"pidof {pkg}")
        return len(pid) > 0

    def list_packages(self) -> list:
        """Memindai sistem secara instan untuk mencari semua package yang terinstal dengan unsur 'roblox'."""
        raw_packages = self.run("pm list packages")
        return self._parse_package_list(raw_packages, keyword="roblox")

    def list_package_names(self, keyword: str = None) -> list:
        raw_packages = self.run_plain("pm list packages")
        return self._parse_package_list(raw_packages, keyword=keyword)

    def get_package_version(self, package_name: str) -> str:
        output = self.run_plain(f"dumpsys package {package_name} | grep versionName")
        if output:
            parts = output.split('=')
            if len(parts) > 1:
                return parts[1].strip()
        return "Unknown"

    def get_system_property(self, prop_name: str) -> str:
        val = self.run_plain(f"getprop {prop_name}", timeout=5)
        return val if val else "Unknown"

    def clear_cache(self, target_pkg: str = ""):
        self.run_plain("rm -rf ~/.cache/*")
        if target_pkg:
            self.run_plain(f"pm clear {target_pkg} cache", timeout=5)

    def _parse_package_list(self, raw_packages: str, keyword: str = None) -> list:
        clones = []
        for line in raw_packages.split("\n"):
            if line.startswith("package:"):
                pkg = line.replace("package:", "").strip()
                if not keyword or keyword.lower() in pkg.lower():
                    clones.append(pkg)
        return sorted(clones)
