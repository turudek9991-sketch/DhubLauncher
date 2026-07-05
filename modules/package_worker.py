import threading
import time

from modules.status import PackageStatus


class PackageWorker:
    def __init__(
        self,
        package: str,
        coordinate: dict,
        place_id: str,
        process_manager,
        xml_manager,
        retry_manager,
        status_store: dict,
        logger,
        check_interval: float = 2.0,
        launch_check_delay: float = 15.0
    ):
        self.package = package
        self.coordinate = coordinate
        self.place_id = place_id
        self.proc = process_manager
        self.xml_mgr = xml_manager
        self.retry_mgr = retry_manager
        self.status_store = status_store
        self.logger = logger
        self.check_interval = check_interval
        self.launch_check_delay = launch_check_delay
        self.running = threading.Event()
        self.thread = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return

        self.running.set()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running.clear()

    def set_status(self, status: PackageStatus):
        self.status_store[self.package] = status

    def run(self):
        while self.running.is_set():
            if self.proc.is_running(self.package):
                self.retry_mgr.reset()
                self.set_status(PackageStatus.Online)
                time.sleep(self.check_interval)
                continue

            current_status = self.status_store.get(self.package)
            if current_status in [PackageStatus.Online, PackageStatus.Launching, PackageStatus.Error]:
                self.set_status(PackageStatus.Restarting)
            else:
                self.set_status(PackageStatus.Loading)

            self.proc.force_stop(self.package)
            time.sleep(0.5)

            self.xml_mgr.inject(self.package, self.coordinate)

            self.set_status(PackageStatus.Launching)
            self.proc.launch_package(self.package, self.place_id)

            self._sleep_with_stop(self.launch_check_delay)
            if not self.running.is_set():
                break

            if self.proc.is_running(self.package):
                self.retry_mgr.reset()
                self.set_status(PackageStatus.Online)
            else:
                self.retry_mgr.record_failure()
                self.set_status(PackageStatus.Error)
                self.retry_mgr.wait_if_needed(self.running)
                self._sleep_with_stop(self.check_interval)

    def _sleep_with_stop(self, seconds: float):
        end_time = time.time() + seconds
        while self.running.is_set() and time.time() < end_time:
            time.sleep(0.2)
