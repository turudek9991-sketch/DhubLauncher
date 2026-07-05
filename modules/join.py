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

from rich.align import Align
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel

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
        
        # Instance LauncherEngine yang sudah ada dari MainMenu
        self.launcher_engine = launcher_engine

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
        """Membangun tabel status instance yang premium dan informatif."""
        table = Table(
            header_style="bold white",
            border_style="dim",
            show_header=True,
            expand=True,
            row_styles=["", "dim"]
        )
        table.add_column("ID", justify="center", style="cyan")
        table.add_column("Package", no_wrap=True, width=40, style="white")
        table.add_column("Status", width=15)
        table.add_column("Retry", justify="center")
        table.add_column("Uptime", justify="center")
        table.add_column("Health", justify="right")

        status_styles = {
            PackageStatus.Online: ("● ONLINE", "bold green"),
            PackageStatus.Launching: ("● LAUNCHING", "bold yellow"),
            PackageStatus.Loading: ("● LOADING", "bold magenta"),
            PackageStatus.Restarting: ("RECOVERING", "bold yellow"),
            PackageStatus.Error: ("ERROR", "bold red"),
            PackageStatus.Offline: ("OFFLINE", "dim white"),
        }

        for idx, pkg in enumerate(clones, 1):
            status_obj = self.clone_statuses.get(pkg, {"status": PackageStatus.Offline, "uptime": 0, "retries": 0, "health": 0})
            status = status_obj.get("status", PackageStatus.Offline)
            status_text, style = status_styles.get(status, ("UNKNOWN", "dim white"))

            uptime_seconds = status_obj.get("uptime", 0)
            uptime_str = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))
            retries = str(status_obj.get("retries", 0))
            health = f"{status_obj.get('health', 0)}%"

            table.add_row(
                str(idx).zfill(2),
                pkg,
                f"[{style}]{status_text}[/]",
                retries,
                uptime_str,
                health
            )
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
╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ 
"""
        
        header = Align.center(
            f"[bold cyan]{header_text}[/bold cyan]\n"
            "[dim white]DHUB LAUNCHER PRO v2.0 • Multi Instance Automation[/dim white]"
        )

        # Placeholder untuk panel info atas, bisa diisi nanti
        info_panel = Panel(
            " ",
            border_style="dim",
            title="[bold white]Engine Status & Device Monitor[/bold white]",
            title_align="left"
        )

        instance_panel = Panel(
            self._generate_status_table(clones),
            border_style="dim",
            title="[bold white]Instance Monitor[/bold white]",
            title_align="left"
        )

        layout.split_column(
            Layout(header, size=9),
            Layout(info_panel, size=5),
            Layout(instance_panel, name="main")
        )
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
            while self.is_monitoring: # Loop monitoring utama
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

        # Tidak perlu clear atau print di sini, karena 'transient=True' akan mengembalikan layar secara otomatis.
