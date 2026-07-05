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
        self.uptime_start = 0
        self.last_heartbeat = 0
        self.current_status = PackageStatus.Offline
        self.health_score = 0

    def start(self):
        if self.thread and self.thread.is_alive():
            return

        self.running.set()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running.clear()

    def set_status(self, status: PackageStatus):
        self.current_status = status
        if status == PackageStatus.Online:
            if self.uptime_start == 0:
                self.uptime_start = time.time()
            self.last_heartbeat = time.time()
        elif status != PackageStatus.Online and self.current_status != PackageStatus.Launching:
             self.uptime_start = 0

        uptime = time.time() - self.uptime_start if self.uptime_start > 0 else 0
        self.status_store[self.package] = {"status": status, "uptime": uptime, "retries": self.retry_mgr.failed_attempts, "health": self.health_score}

    def _heal(self):
        """
        Self-healing relaunch untuk package INI SAJA: force-stop -> inject XML -> am start.
        Dipanggil hanya ketika package ini terdeteksi mati - tidak pernah menyentuh clone lain.
        """
        self.uptime_start = 0 # Reset uptime on heal
        if self.current_status in [PackageStatus.Online, PackageStatus.Launching, PackageStatus.Error]:
            self.set_status(PackageStatus.Restarting)
        else:
            self.set_status(PackageStatus.Loading)

        self.proc.force_stop(self.package)
        time.sleep(0.5)

        self.logger.info(f"[{self.package}] Injecting XML grid coordinates...")
        self.xml_mgr.inject(self.package, self.coordinate)

        self.set_status(PackageStatus.Launching)
        self.proc.launch_package(self.package, self.place_id)

    def _check_health(self) -> tuple[bool, str]:
        """
        Mesin deteksi kesehatan yang lebih canggih.
        Mengembalikan (is_healthy: bool, reason: str).
        """
        self.health_score = 0

        # 1. Process Detector (bobot 25%)
        if not self.proc.is_running(self.package):
            return False, "Process not found (pidof failed)"
        self.health_score += 25

        # 2. Window Detector (bobot 25%)
        # Periksa apakah ada window yang ditampilkan untuk paket ini.
        window_dump = self.proc.run(f"dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp' | grep {self.package}")
        if not window_dump:
            return False, "Window not focused or visible"
        self.health_score += 25

        # 3. UI Detector (bobot 50%) - Paling penting
        # Periksa teks error pada UI. Ini adalah panggilan yang mahal, jangan terlalu sering.
        # Kita akan menggunakan `dumpsys activity top` sebagai proxy yang lebih cepat
        activity_top = self.proc.run("dumpsys activity top")
        error_keywords = ["Reconnect", "Leave", "Disconnected", "Connection Lost", "Connection Failed", "Try Again", "Error 277", "Error 278", "Error 279"]
        for keyword in error_keywords:
            if keyword in activity_top:
                 # Pastikan error ini relevan dengan window kita
                 if self.package in self.proc.run("dumpsys window windows | grep mCurrentFocus"):
                    return False, f"UI Error Detected: '{keyword}'"
        self.health_score += 50

        # 4. Heartbeat Detector (implisit)
        if self.last_heartbeat > 0 and (time.time() - self.last_heartbeat > 60):
            return False, "App frozen (heartbeat lost)"

        return True, "All checks passed"

    def run(self):
        self.set_status(PackageStatus.Offline)
        self._sleep_with_stop(self.launch_check_delay)

        while self.running.is_set():
            is_healthy, reason = self._check_health()

            if is_healthy:
                self.retry_mgr.reset()
                self.set_status(PackageStatus.Online)
                self._sleep_with_stop(self.check_interval)
                continue

            # APLIKASI TIDAK TERDETEKSI: Langsung lakukan proses healing tanpa debounce.
            self.logger.error(f"[{self.package}] Unhealthy: {reason}. Initiating self-healing protocol.")
            self.retry_mgr.record_failure()
            if self.retry_mgr.is_exceeded():
                self.logger.error(f"[{self.package}] Max retries exceeded. Marking as ERROR.")
                self.set_status(PackageStatus.Error)
                self.retry_mgr.wait_if_needed(self.running) # Masuk cooldown panjang
                continue

            self._heal()
            self._sleep_with_stop(self.launch_check_delay)

    def _sleep_with_stop(self, seconds: float):
        end_time = time.time() + seconds
        while self.running.is_set() and time.time() < end_time:
            time.sleep(0.2)
