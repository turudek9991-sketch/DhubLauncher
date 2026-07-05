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
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

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

    def _generate_main_table(self, clones: list) -> Table:
        """Membangun tabel utama yang berisi semua informasi UI."""
        table = Table(
            box=None,
            expand=False,
            padding=0,
            show_header=False
        )
        table.add_column("main_content")

        # --- Header ---
        header_text = Text("\nDHUB LAUNCHER PRO\n", style="bold cyan")
        header_text.append("Autonomous Multi-Instance Engine\n", style="dim white")
        table.add_row(header_text)
        table.add_row(Text("─" * 50, style="dim"))

        status_styles = {
            PackageStatus.Online: ("● ONLINE", "bold green"),
            PackageStatus.Launching: ("● LAUNCHING", "bold yellow"),
            PackageStatus.Loading: ("● LOADING", "bold magenta"),
            PackageStatus.Restarting: ("RECOVERING", "bold yellow"),
            PackageStatus.Error: ("ERROR", "bold red"),
            PackageStatus.Offline: ("OFFLINE", "dim white"),
        }

        # --- Instance Monitor Table ---
        instance_table = Table(box=None, show_header=True, header_style="bold dim white", expand=False)
        instance_table.add_column("ID", width=3)
        instance_table.add_column("PACKAGE", width=25, no_wrap=True)
        instance_table.add_column("STATUS", width=12)
        instance_table.add_column("UPTIME", width=10, justify="right")

        for idx, pkg in enumerate(clones, 1):
            status_obj = self.clone_statuses.get(pkg, {"status": PackageStatus.Offline, "uptime": 0, "retries": 0, "health": 0})
            status = status_obj.get("status", PackageStatus.Offline)
            status_text, style = status_styles.get(status, ("UNKNOWN", "dim white"))
            uptime_seconds = status_obj.get("uptime", 0)
            uptime_str = time.strftime('%H:%M:%S', time.gmtime(uptime_seconds))

            instance_table.add_row(
                str(idx).zfill(2),
                pkg.replace("com.roblox.", ""), # Ringkas nama package
                f"[{style}]{status_text}[/]",
                uptime_str
            )
        
        table.add_row(Panel(instance_table, border_style="dim", title="Instance Monitor", title_align="left"))

        # --- Footer ---
        healthy_workers = sum(1 for s in self.clone_statuses.values() if s.get("status") == PackageStatus.Online)
        total_workers = len(clones)
        footer_text = Text(f"Workers: {healthy_workers}/{total_workers}  |  Self-Healing: ACTIVE\n", style="dim white")
        footer_text.append("Press CTRL+C to exit monitoring", style="bold dim white")
        table.add_row(Text("─" * 50, style="dim"))
        table.add_row(footer_text)

        return table

    def launch_app(self):
        place_id = self.config_mgr.config_data.get("place_id", "")

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
        with Live(self._generate_main_table(installed_clones), screen=True, transient=True, refresh_per_second=2) as live:
            # TODO: Add keyboard listener to exit with 'q'
            while self.is_monitoring: # Loop monitoring utama
                try:
                    self.clone_statuses = self.launcher_engine.get_statuses()
                    live.update(self._generate_main_table(installed_clones))
                    time.sleep(0.5)
                except KeyboardInterrupt:
                    self.is_monitoring = False
                    break
        
        # Cleanup
        if self.is_monitoring:
            self.is_monitoring = False
            # JANGAN panggil stop() di sini agar worker tetap berjalan di background

        # Tidak perlu clear atau print di sini, karena 'transient=True' akan mengembalikan layar secara otomatis.
