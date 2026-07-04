import subprocess

class ProcessManager:
    def __init__(self, logger):
        self.logger = logger

    def run(self, cmd: str) -> str:
        try:
            # Semua akses root terpusat di sini
            result = subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Root Execution failed: {e}")
            return ""

    def force_stop(self, pkg: str):
        self.run(f"am force-stop {pkg}")

    def is_running(self, pkg: str) -> bool:
        return len(self.run(f"pidof {pkg}")) > 0

    def launch(self, pkg: str, place_id: str = None):
        if place_id:
            cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {pkg}"
        else:
            main_act = self.run(f"cmd package resolve-activity --brief {pkg} | tail -n 1")
            cmd = f"am start -n {main_act}" if "/" in main_act else f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
        self.run(cmd)

    def list_clones(self) -> list:
        raw = self.run("pm list packages")
        return sorted([line.replace("package:", "").strip() for line in raw.split("\n") if "roblox" in line.lower()])
