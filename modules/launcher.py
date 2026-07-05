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

        for idx, pkg in enumerate(clones):
            if not self.running:
                break

            coordinate = self.grid_mgr.calculate_xml_coordinates(idx)
            worker = PackageWorker(
                package=pkg,
                coordinate=coordinate,
                place_id=place_id,
                process_manager=self.proc,
                xml_manager=self.xml_mgr,
                retry_manager=RetryManager(),
                status_store=self.clone_statuses,
                logger=self.logger
            )
            self.workers[pkg] = worker
            worker.start()

            if idx < total - 1:
                time.sleep(delay_cfg)

    def stop(self):
        self.running = False
        for worker in self.workers.values():
            worker.stop()

    def get_statuses(self) -> dict:
        return self.clone_statuses
