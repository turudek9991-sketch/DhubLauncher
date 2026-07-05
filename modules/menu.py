"""
DHub-Rejoin - Menu Module (Fixed Buffer & Anti-Kickback)
Author: Senior Python Developer
Description: Handles the interactive main menu and routes user selections strictly based on choice.
"""

import sys
import time
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.prompt import Prompt

# Import local modules
from modules.package import PackageManager
from modules.settings import SettingsManager
from modules.join import JoinManager
from modules.arrange import ArrangeManager
from modules.launcher import LauncherEngine
from modules.optimize import OptimizeManager
from modules.webhook import WebhookManager
from modules.utils import UtilsManager

console = Console()

class MainMenu:
    def __init__(self, config_mgr, logger):
        self.config_mgr = config_mgr
        self.logger = logger
        
        # Buat LauncherEngine di sini agar persisten selama aplikasi berjalan
        self.launcher_engine = LauncherEngine(config_mgr, logger)
        
        # Inisialisasi sub-modul aman tanpa memicu fungsi internal
        self.package_mgr = PackageManager(config_mgr, logger)
        self.settings_mgr = SettingsManager(config_mgr, logger)
        # Berikan instance LauncherEngine yang sudah ada ke JoinManager
        self.join_mgr = JoinManager(config_mgr, logger, self.launcher_engine)
        self.arrange_mgr = ArrangeManager(config_mgr, logger)
        self.optimize_mgr = OptimizeManager(config_mgr, logger)
        self.webhook_mgr = WebhookManager(config_mgr, logger)
        self.utils_mgr = UtilsManager(config_mgr, logger)

    def display_main_menu(self) -> str:
        """
        Menampilkan menu utama ke terminal dengan layout modern.
        """
        menu_items = {
            "1": "Launch All Roblox",
            "2": "Package Manager",
            "3": "Optimize Storage",
            "4": "Device Information",
            "5": "Settings",
            "6": "Discord Webhook",
            "7": "View Logs",
            "0": "Exit"
        }

        menu_text = Text(justify="left")
        for key, value in menu_items.items():
            menu_text.append(f"    [bold cyan]{key.zfill(2)}[/bold cyan] [white]▶[/white] [dim white]{value}[/dim white]\n\n")

        header = (
            "\n[bold white]DHUB LAUNCHER PRO[/bold white]\n\n"
            "[dim white]Professional Roblox Multi Launcher[/dim white]\n"
        )

        panel = Panel(
            menu_text,
            title=header,
            title_align="center",
            border_style="cyan",
            expand=False,
            padding=(1, 2)
        )

        console.print(panel)

        choice = Prompt.ask(
            " [dim white]Select Menu >[/dim white]",
            choices=["1", "2", "3", "4", "5", "6", "7", "0"],
            default="1"
        )
        return choice

    def execute_choice(self, choice: str) -> bool:
        """
        Mengeksekusi fungsi HANYA ketika angka menu dipilih oleh user secara ketat.
        """
        if choice == "1":
            self.logger.info("Executing: Launch Application")
            self.join_mgr.launch_app()
        elif choice == "2":
            self.logger.info("Executing: Package Manager Scan")
            self.package_mgr.manage_packages()
        elif choice == "3":
            self.logger.info("Executing: Optimize Storage")
            self.optimize_mgr.clean_cache()
        elif choice == "4":
            self.logger.info("Executing: Device Info")
            self.arrange_mgr.display_device_info()
        elif choice == "5":
            self.logger.info("Executing: Settings")
            self.settings_mgr.open_settings()
        elif choice == "6":
            self.logger.info("Executing: Discord Test")
            self.webhook_mgr.test_webhook()
        elif choice == "7":
            self.logger.info("Executing: View Logs")
            self.utils_mgr.view_logs()
        elif choice == "0":
            console.print("\n[bold red][!] Shutdown Core Engine. Bye![/bold red]")
            return False
            
        # PENCEGAHAN MENTAL: Bersihkan buffer input sebelum menahan layar
        # Hentikan engine hanya jika keluar dari aplikasi, bukan dari menu join
        if choice != "0":
            try:
                sys.stdin.flush() # Flush sisa enter gaib di Termux
            except Exception:
                pass
            print("\n")
            console.print("[dim white]─────────────────────────────────────────────────[/dim white]")
            Prompt.ask("[bold green]Tekan Enter untuk kembali ke Menu Utama[/bold green]", choices=[], default="")
        else:
            self.launcher_engine.stop()
            
        return True
