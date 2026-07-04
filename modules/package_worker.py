import threading, time
from modules.status import WorkerStatus

class PackageWorker(threading.Thread):
    def __init__(self, pkg, index, proc, xml, grid, retry, logger):
        super().__init__(daemon=True)
        self.pkg, self.index, self.proc, self.xml, self.grid, self.retry, self.logger = \
            pkg, index, proc, xml, grid, retry, logger
        self.status = WorkerStatus.OFFLINE
        self.running = True

    def run(self):
        while self.running:
            if not self.proc.is_running(self.pkg):
                if self.retry.is_limit_reached():
                    self.status = WorkerStatus.ERROR
                    time.sleep(self.retry.get_cooldown_time())
                    self.retry.reset()
                else:
                    self.status = WorkerStatus.RESTARTING
                    self.proc.force_stop(self.pkg)
                    coords = self.grid.get_coordinates(self.index)
                    self.xml.inject(self.pkg, coords)
                    self.proc.launch(self.pkg)
                    self.retry.increment()
                    self.status = WorkerStatus.LOADING
            else:
                self.status = WorkerStatus.ONLINE
                self.retry.reset()
            time.sleep(5)
