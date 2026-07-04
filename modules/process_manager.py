import subprocess

class ProcessManager:
    def __init__(self, logger):
        self.logger = logger

    def run(self, cmd, timeout=10):
        """Eksekusi perintah shell dengan akses root."""
        try:
            full_cmd = f"su -c '{cmd}'"
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                self.logger.debug(f"Command failed: {cmd} | Error: {result.stderr}")
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Process Execution Error: {e}")
            return ""

    def force_stop(self, pkg_name):
        self.run(f"am force-stop {pkg_name}")

    def is_running(self, pkg_name):
        return len(self.run(f"pidof {pkg_name}")) > 0

    def launch_package(self, pkg_name, place_id=None):
        if place_id:
            cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {pkg_name} --activity-brought-to-front"
        else:
            main_act = self.run(f"cmd package resolve-activity --brief {pkg_name} | tail -n 1")
            cmd = f"am start -n {main_act} --activity-brought-to-front" if "/" in main_act else f"monkey -p {pkg_name} -c android.intent.category.LAUNCHER 1"
        self.run(cmd)

    def list_packages(self):
        raw = self.run("pm list packages")
        return [line.replace("package:", "").strip() for line in raw.split('\n') if "roblox" in line.lower()]
