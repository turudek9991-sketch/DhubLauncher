import time
from modules.package_worker import PackageWorker

class LauncherEngine:
    def __init__(self, config_mgr, logger, grid_cfg):
        self.config_mgr = config_mgr
        self.logger = logger
        self.grid_cfg = grid_cfg
        self.workers = {}

    def get_all_roblox_clones(self):
        # Mengambil logika scan package (akan kita pindahkan ke ProcessManager nanti)
        import subprocess
        try:
            raw = subprocess.check_output("su -c 'pm list packages'", shell=True).decode()
            return sorted([line.replace("package:", "").strip() for line in raw.split('\n') if "roblox" in line.lower()])
        except:
            return []

    def start_all(self):
        clones = self.get_all_roblox_clones()
        self.logger.info(f"Starting Engine for {len(clones)} instances")
        
        for idx, pkg in enumerate(clones):
            # Inisialisasi worker untuk setiap package
            worker = PackageWorker(
                pkg_name=pkg,
                index=idx,
                config_mgr=self.config_mgr,
                logger=self.logger,
                grid_config=self.grid_cfg,
                launch_callback=self._execute_launch,
                inject_callback=self._execute_inject
            )
            self.workers[pkg] = worker
            worker.start()
            time.sleep(2) # Delay antar peluncuran

    def _execute_launch(self, pkg_name):
        # Placeholder untuk pemanggilan launcher system
        self.logger.info(f"Launching {pkg_name}...")
        # Integrasi dengan perintah shell akan dipindah ke ProcessManager nanti

    def _execute_inject(self, pkg_name):
        # Placeholder untuk pemanggilan XML Manager
        self.logger.info(f"Injecting XML for {pkg_name}...")

    def stop_all(self):
        for worker in self.workers.values():
            worker.stop()
        self.workers.clear()
