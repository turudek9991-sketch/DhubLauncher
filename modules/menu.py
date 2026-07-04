"""
DHub-Rejoin - Menu Module
Author: Senior Python Developer
Description: Handles the interactive main menu and routes user selections to proper modules.
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Import local modules
from modules.package import PackageManager
from modules.settings import SettingsManager
from modules.join import JoinManager
from modules.arrange import ArrangeManager
from modules.optimize import OptimizeManager
from modules.webhook import WebhookManager
from modules.utils import UtilsManager

console = Console()

class MainMenu:
    def __init__(self, config_mgr, logger):
        """
        Inisialisasi MainMenu dengan dependensi yang dibutuhkan.
        """
        self.config_mgr = config_mgr
        self.logger = logger
        
        # Inisialisasi sub-modul
        self.package_mgr = PackageManager(config_mgr, logger)
        self.settings_mgr = SettingsManager(config_mgr, logger)
        self.join_mgr = JoinManager(config_mgr, logger)
        self.arrange_mgr = ArrangeManager(config_mgr, logger)
        self.optimize_mgr = OptimizeManager(config_mgr, logger)
        self.webhook_mgr = WebhookManager(config_mgr, logger)
        self.utils_mgr = UtilsManager(config_mgr, logger)

    def display_main_menu(self) -> str:
        """
        Menampilkan menu utama ke terminal menggunakan Rich Panel dan mengembalikan input user.
        """
        menu_text = (
            "[bold cyan]1.[/bold cyan] Launch Application (Join)\n"
            "[bold cyan]2.[/bold cyan] Package Manager\n"
            "[bold cyan]3.[/bold cyan] Optimize Storage\n"
            "[bold cyan]4.[/bold cyan] Device Information (Arrange)\n"
            "[bold cyan]5.[/bold cyan] Settings\n"
            "[bold cyan]6.[/bold cyan] Discord Webhook Test\n"
            "[bold cyan]7.[/bold cyan] View Logs\n"
            "[bold cyan]8.[/bold cyan] Exit"
        )
        
        console.print(Panel(menu_text, title="[bold green]MAIN MENU[/bold green]", border_style="bright_blue", expand=False))
        
        choice = Prompt.ask(
            "[bold yellow]Pilih opsi (1-8)[/bold yellow]", 
            choices=["1", "2", "3", "4", "5", "6", "7", "8"], 
            default="1"
        )
        return choice

    def execute_choice(self, choice: str) -> bool:
        """
        Mengeksekusi fungsi berdasarkan pilihan user.
        Mengembalikan True jika program lanjut berjalan, dan False jika user memilih keluar (Exit).
        """
        if choice == "1":
            self.logger.info("User selected: Launch Application")
            self.join_mgr.launch_app()
            
        elif choice == "2":
            self.logger.info("User selected: Package Manager")
            self.package_mgr.manage_packages()
            
        elif choice == "3":
            self.logger.info("User selected: Optimize Storage")
            self.optimize_mgr.clean_cache()
            
        elif choice == "4":
            self.logger.info("User selected: Device Information")
            self.arrange_mgr.display_device_info()
            
        elif choice == "5":
            self.logger.info("User selected: Settings")
            self.settings_mgr.open_settings()
            
        elif choice == "6":
            self.logger.info("User selected: Discord Webhook Test")
            self.webhook_mgr.test_webhook()
            
        elif choice == "7":
            self.logger.info("User selected: View Logs")
            self.utils_mgr.view_logs()
            
        elif choice == "8":
            console.print("\n[bold red]Keluar dari DHub-Rejoin. Sampai jumpa![/bold red]")
            return False
            
        # Menahan layar setelah eksekusi menu selesai agar user bisa membaca output
        if choice != "8":
            input("\nTekan Enter untuk kembali ke Menu Utama...")
            
        return True
