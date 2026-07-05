import time

from modules.grid_manager import GridManager
from modules.package_worker import PackageWorker
from modules.process_manager import ProcessManager
from modules.retry_manager import RetryManager
from modules.status import PackageStatus
from modules.xml_manager import XMLManager


class LauncherEngine:
    def __init__(self, config_mgr, logger, process_manager=None, grid_manager=None, xml_manager=None):
        self.config_mgr = config_mgr
        self.logger = logger
        self.proc = process_manager or ProcessManager(logger)
        self.grid_mgr = grid_manager or GridManager()
        self.xml_mgr = xml_manager or XMLManager(self.proc)
        self.workers = {}
        self.clone_statuses = {}
        self.running = False

    def scan_packages(self) -> list:
        return self.proc.list_packages()

    def _launch_one(self, pkg: str, coordinate: dict, place_id: str):
        """
        Satu siklus launch berat untuk satu package: force-stop -> inject XML -> am start.
        Urutan dan timing dijaga identik dengan join.py versi lama yang sudah terbukti stabil.
        """
        self.clone_statuses[pkg] = PackageStatus.Loading
        self.proc.force_stop(pkg)
        time.sleep(0.5)

        self.xml_mgr.inject(pkg, coordinate)

        self.clone_statuses[pkg] = PackageStatus.Launching
        self.proc.launch_package(pkg, place_id)

    def start(self, place_id: str = "", packages: list = None):
        if self.running:
            return

        clones = packages if packages is not None else self.scan_packages()
        self.running = True
        self.clone_statuses.clear()
        self.workers.clear()

        for pkg in clones:
            self.clone_statuses[pkg] = PackageStatus.Offline

        total = len(clones)
        delay_cfg = 5
        coordinates = {}

        # FASE 1 - INITIAL LAUNCH (sequential, satu thread, identik dengan versi lama)
        # Sengaja TIDAK diparalelkan. Root/su call yang konkuren antar package inilah
        # yang menyebabkan Roblox gagal terbuka setelah refactor sebelumnya.
        for idx, pkg in enumerate(clones):
            if not self.running:
                break

            coordinate = self.grid_mgr.calculate_xml_coordinates(idx)
            coordinates[pkg] = coordinate

            self._launch_one(pkg, coordinate, place_id)

            if idx < total - 1:
                time.sleep(delay_cfg)

        # FASE 2 - SELF-HEALING MONITOR (per package, dimulai HANYA setelah fase 1 selesai)
        # Tiap worker hanya memantau dan menyembuhkan packagenya sendiri saat crash.
        # Tidak pernah me-restart semua instance sekaligus.
        for pkg in clones:
            if not self.running:
                break

            worker = PackageWorker(
                package=pkg,
                coordinate=coordinates[pkg],
                place_id=place_id,
                process_manager=self.proc,
                xml_manager=self.xml_mgr,
                retry_manager=RetryManager(),
                status_store=self.clone_statuses,
                logger=self.logger
            )
            self.workers[pkg] = worker
            worker.start()

    def stop(self):
        self.running = False
        for worker in self.workers.values():
            worker.stop()

    def get_statuses(self) -> dict:
        return self.clone_statuses
