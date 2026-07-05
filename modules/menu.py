"""
DHub-Rejoin - Menu Module (Fixed Buffer & Anti-Kickback)
Author: Senior Python Developer
Description: Handles the interactive main menu and routes user selections strictly based on choice.
"""

import sys
import time
from rich.console import Console
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
        menu_text = (
            "[bold cyan][01][/bold cyan] Launch Application (Auto Rejoin)\n"
            "[bold cyan][02][/bold cyan] Scan & Auto-Save Package\n"
            "[bold cyan][03][/bold cyan] Optimize Storage (Clear Cache)\n"
            "[bold cyan][04][/bold cyan] Device Information Report\n"
            "[bold cyan][05][/bold cyan] Settings Configuration\n"
            "[bold cyan][06][/bold cyan] Discord Webhook Connectivity Test\n"
            "[bold cyan][07][/bold cyan] View System Logs Stream\n"
            "[bold cyan][08][/bold cyan] Exit Core Engine"
        )
        
        console.print(Panel(menu_text, title="[bold green] CONTROL PANEL [/bold green]", border_style="cyan", expand=False))
        
        choice = Prompt.ask(
            "[bold yellow]DHub Input[/bold yellow]", 
            choices=["1", "2", "3", "4", "5", "6", "7", "8"], 
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
            self.logger.info("Executing: Settings Submenu")
            self.settings_mgr.open_settings()
        elif choice == "6":
            self.logger.info("Executing: Discord Test")
            self.webhook_mgr.test_webhook()
        elif choice == "7":
            self.logger.info("Executing: View Logs")
            self.utils_mgr.view_logs()
        elif choice == "8":
            console.print("\n[bold red][!] Shutdown Core Engine. Bye![/bold red]")
            return False
            
        # PENCEGAHAN MENTAL: Bersihkan buffer input sebelum menahan layar
        # Hentikan engine hanya jika keluar dari aplikasi, bukan dari menu join
        if choice != "8":
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
