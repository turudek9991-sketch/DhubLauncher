import threading
import time

from modules.status import PackageStatus


class PackageWorker:
    """Worker terisolasi yang memonitor dan menyembuhkan satu package aplikasi."""
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
        check_interval: float = 3.0,
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

    def _heal(self):
        """
        Self-healing relaunch untuk package INI SAJA: force-stop -> inject XML -> am start.
        Dipanggil hanya ketika package ini terdeteksi mati - tidak pernah menyentuh clone lain.
        """
        current_status = self.status_store.get(self.package)
        if current_status in [PackageStatus.Online, PackageStatus.Launching, PackageStatus.Error]:
            self.set_status(PackageStatus.Restarting)
        else:
            self.set_status(PackageStatus.Loading)

        self.proc.force_stop(self.package)
        time.sleep(0.5)

        self.logger.info(f"[{self.package}] Injecting XML grid coordinates...")
        self.xml_mgr.inject(self.package, self.coordinate)

        self.set_status(PackageStatus.Launching)
        self.proc.launch_package(self.package, self.place_id)

    def run(self):
        # Grace period: launch awal untuk package ini sudah dilakukan secara sequential
        # oleh LauncherEngine SEBELUM thread monitor ini dimulai. Beri waktu agar
        # benar-benar online sebelum dievaluasi, supaya tidak langsung dianggap mati.
        self._sleep_with_stop(self.launch_check_delay)

        debounce_count = 0
        max_debounce = 3 # Aplikasi harus mati 3 kali berturut-turut untuk dikonfirmasi

        while self.running.is_set():
            if self.proc.is_running(self.package):
                self.retry_mgr.reset()
                debounce_count = 0
                self.set_status(PackageStatus.Online)
                self._sleep_with_stop(self.check_interval)
                continue

            # DEBOUNCE: Proses tidak terdeteksi, mulai hitung.
            debounce_count += 1
            self.logger.warning(f"[{self.package}] Offline detection count: {debounce_count}/{max_debounce}")

            if debounce_count < max_debounce:
                self._sleep_with_stop(self.check_interval)
                continue

            # CONFIRMED OFFLINE: Lakukan proses healing.
            self.logger.error(f"[{self.package}] Confirmed OFFLINE. Initiating self-healing protocol.")
            self._heal()
            debounce_count = 0 # Reset debounce setelah heal

            # Beri waktu aplikasi untuk startup sebelum loop verifikasi berikutnya
            self._sleep_with_stop(self.launch_check_delay)

            if self.proc.is_running(self.package):
                self.retry_mgr.reset()
                self.set_status(PackageStatus.Online)
            else:
                self.retry_mgr.record_failure()
                self.set_status(PackageStatus.Error) # Set status Error jika gagal restart
                self.logger.error(f"[{self.package}] Heal failed. Entering cooldown. Attempts: {self.retry_mgr.failed_attempts}")
                self.retry_mgr.wait_if_needed(self.running)

    def _sleep_with_stop(self, seconds: float):
        end_time = time.time() + seconds
        while self.running.is_set() and time.time() < end_time:
            time.sleep(0.2)
