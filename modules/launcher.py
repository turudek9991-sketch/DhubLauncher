from modules.package_worker import PackageWorker
from modules.retry_manager import RetryManager

class LauncherEngine:
    def __init__(self, proc, xml, grid, logger):
        self.proc, self.xml, self.grid, self.logger = proc, xml, grid, logger
        self.workers = {}

    def start_all(self):
        clones = self.proc.list_clones()
        for i, pkg in enumerate(clones):
            worker = PackageWorker(pkg, i, self.proc, self.xml, self.grid, RetryManager(), self.logger)
            self.workers[pkg] = worker
            worker.start()
