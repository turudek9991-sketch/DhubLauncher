import threading
import time
import subprocess

class PackageWorker(threading.Thread):
    def __init__(self, pkg_name, config_mgr, logger, launch_callback, inject_callback):
        super().__init__(daemon=True)
        self.pkg_name = pkg_name
        self.config_mgr = config_mgr
        self.logger = logger
        self.launch_callback = launch_callback   # Fungsi untuk menjalankan package
        self.inject_callback = inject_callback   # Fungsi untuk inject XML
        
        self.status = "Offline"
        self.retry_count = 0
        self.running = True

    def _execute(self, cmd):
        try:
            return subprocess.run(f"su -c '{cmd}'", shell=True, capture_output=True, text=True, timeout=10).stdout.strip()
        except: return ""

    def is_running(self):
        return len(self._execute(f"pidof {self.pkg_name}")) > 0

    def run(self):
        self.logger.info(f"Worker started for {self.pkg_name}")
        while self.running:
            if not self.is_running():
                if self.status != "Loading":
                    self.status = "Restarting" if self.retry_count > 0 else "Loading"
                
                if self.retry_count >= 5:
                    self.status = "Error"
                    time.sleep(30)
                    self.retry_count = 0
                else:
                    self.perform_recovery()
            else:
                self.status = "Online"
                self.retry_count = 0
            time.sleep(5)

    def perform_recovery(self):
        self.retry_count += 1
        self.status = "Launching"
        self._execute(f"am force-stop {self.pkg_name}")
        self.inject_callback(self.pkg_name)
        self.launch_callback(self.pkg_name)
        time.sleep(5)

    def stop(self):
        self.running = False
