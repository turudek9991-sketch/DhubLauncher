"""
DHub-Rejoin - Premium Join & Monitoring Interface
Author: Senior Python Developer
Description: Provides a professional, real-time monitoring dashboard for all running instances,
             built with Rich for a flicker-free, premium user experience.
"""

import time
import os
import threading

from modules.grid_manager import GridManager
from modules.launcher import LauncherEngine
from modules.process_manager import ProcessManager
from modules.status import PackageStatus
from modules.xml_manager import XMLManager

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout

class JoinManager:
    def __init__(self, config_mgr, logger, launcher_engine: LauncherEngine):
        self.config_mgr = config_mgr
        self.logger = logger
        
        from modules.webhook import WebhookManager
        from modules.arrange import ArrangeManager

        self.webhook_mgr = WebhookManager(config_mgr, logger)
        self.arrange_mgr = ArrangeManager(config_mgr, logger)
        self.proc = ProcessManager(logger)
        
        self.is_monitoring = False
        self.clone_statuses = {}
        
        # [SUPER COMPACT KAERU MATRIX - DPI 600 HARD LOCK]
        # Ukuran dan margin disusutkan maksimal agar fit sempurna di frame Redfinger
        self.grid_config = {
            "start_x_base": 660,        # Geser merapat ke Termux agar sisi kanan tidak luber keluar frame
            "window_width": 180,        # SUPER MINI: Lebar proporsional window melayang
            "window_height": 100,       # SUPER MINI: Tinggi proporsional window melayang
            "columns": 2,               # Formasi tetap 2 kolom ke samping di wilayah kanan
            "top_margin": 60,           # Batas aman dari status bar atas
            "gap": 5                    # Celah minimalis antar jendela
        }
        self.grid_mgr = GridManager(self.grid_config)
        self.xml_mgr = XMLManager(self.proc)
        self.launcher_engine = launcher_engine

        # SUNTIKKAN manajer yang benar ke engine yang sudah ada!
        self.launcher_engine.set_managers(grid_manager=self.grid_mgr, xml_manager=self.xml_mgr)
        
        try:
            self.config_mgr.set_value("launch_delay", 5)
        except Exception:
            if hasattr(self.config_mgr, 'config_data'):
                self.config_mgr.config_data["launch_delay"] = 5

    def get_all_roblox_clones(self) -> list:
        return self.launcher_engine.scan_packages()

    def is_package_running(self, pkg_name: str) -> bool:
        return self.proc.is_running(pkg_name)

    def launch_all_instances(self, clones: list, place_id: str):
        # Hanya jalankan 'start' jika engine belum berjalan (launch pertama kali)
        if not self.launcher_engine.running:
            self.launcher_engine.start(place_id=place_id, packages=clones)
        else:
            self.logger.info("Launcher engine is already running. Skipping initial launch.")

    def _generate_status_table(self, clones: list) -> Table:
        """Membuat tabel status instance yang modern dan bersih."""
        table = Table(box=None, expand=True)
        table.add_column("PACKAGE", style="cyan", no_wrap=True, width=45)
        table.add_column("STATUS", style="white", width=15)
        table.add_column("PID", style="dim white", justify="left")

        status_styles = {
            PackageStatus.Online: ("● Online", "bold green"),
            PackageStatus.Launching: ("● Launching", "bold yellow"),
            PackageStatus.Loading: ("● Loading", "bold magenta"),
            PackageStatus.Restarting: ("● Restarting", "bold yellow"),
            PackageStatus.Error: ("● Error", "bold red"),
            PackageStatus.Offline: ("● Offline", "dim white"),
        }

        for pkg in clones:
            status = self.clone_statuses.get(pkg, PackageStatus.Offline)
            status_text, style = status_styles.get(status, ("● Unknown", "dim white"))
            
            pid = self.proc.run(f"pidof {pkg}").strip() or "----"

            table.add_row(pkg, f"[{style}]{status_text}[/]", pid)
        
        return table

    def _generate_layout(self, clones: list, ram_info: str) -> Layout:
        """Membangun layout TUI yang dinamis dan premium."""
        layout = Layout()
        header_text = """
██████╗ ██╗  ██╗██╗   ██╗██████╗ 
██╔══██╗██║  ██║██║   ██║██╔══██╗
██║  ██║███████║██║   ██║██████╔╝
██║  ██║██╔══██║██║   ██║██╔══██╗
██████╔╝██║  ██║╚██████╔╝██████╔╝
╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝   [dim white]Launcher v2.0 - @dimsgti[/]
        """
        footer_text = "[dim white]DHUB Launcher Professional Edition | Self Healing Enabled | Press [bold]Q[/bold] to Exit Monitoring[/]"

        layout.split(
            Layout(name="header", size=8),
            Layout(name="main"),
            Layout(name="footer", size=3),
        )
        layout["header"].update(f"[bold cyan]{header_text}[/]")
        layout["main"].update(self._generate_status_table(clones))
        layout["footer"].update(footer_text)
        return layout

    def launch_app(self):
        place_id = self.config_mgr.config_data.get("place_id", "")
        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        installed_clones = self.launcher_engine.scan_packages()
        
        if not installed_clones:
            os.system("clear")
            print("\033[91m[!] Gagal: Tidak ada aplikasi Roblox Clone terdeteksi.\033[0m")
            return

        self.is_monitoring = True
        self.clone_statuses = self.launcher_engine.get_statuses()

        threading.Thread(
            target=self.launch_all_instances,
            args=(installed_clones, place_id),
            daemon=True
        ).start()

        console = Console()
        with Live(self._generate_layout(installed_clones, ram_info), screen=True, transient=True, refresh_per_second=4) as live:
            # TODO: Add keyboard listener to exit with 'q'
            while self.is_monitoring:
                try:
                    self.clone_statuses = self.launcher_engine.get_statuses()
                    live.update(self._generate_layout(installed_clones, ram_info))
                    time.sleep(0.5)
                except KeyboardInterrupt:
                    self.is_monitoring = False
                    break
        
        # Cleanup
        if self.is_monitoring:
            self.is_monitoring = False
            # JANGAN panggil stop() di sini agar worker tetap berjalan di background
            
        os.system("clear")
        print("\033[93m[!] Proses monitoring disinkronkan. Kembali ke menu utama...\033[0m")
        time.sleep(1)
