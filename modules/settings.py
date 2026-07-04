"""
DHub-Rejoin - Settings Management Module (Full Grid Integration)
Author: Senior Python Developer
Description: Provides interactive submenus to update application and Roblox grid configurations dynamically.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
import time

console = Console()

class SettingsManager:
    def __init__(self, config_mgr, logger):
        self.config_mgr = config_mgr
        self.logger = logger

    def display_current_settings(self):
        table = Table(title="Current Configuration Settings", header_style="bold cyan")
        table.add_column("Setting Key", style="yellow")
        table.add_column("Value", style="white")
        
        cfg = self.config_mgr.config_data
        table.add_row("Application Package", str(cfg.get("package", "Not Set")))
        table.add_row("Roblox Place ID (Game)", str(cfg.get("place_id", "Not Set")))
        table.add_row("Launch Delay (sec)", str(cfg.get("launch_delay", 20)))
        table.add_row("Grid Width", str(cfg.get("grid_width", 280)))
        table.add_row("Grid Height", str(cfg.get("grid_height", 200)))
        table.add_row("Grid Start X", str(cfg.get("grid_start_x", 660)))
        table.add_row("Theme", str(cfg.get("theme", "dark")))
        table.add_row("Discord Webhook", str(cfg.get("discord_webhook", "Not Set")))
        
        console.print(table)

    def open_settings(self):
        while True:
            console.clear()
            console.print(Panel("[bold yellow]SETTINGS CONFIGURATION PANEL[/bold yellow]", border_style="yellow"))
            self.display_current_settings()
            
            menu_text = (
                "[bold green]1.[/bold green] Change Application Package Target\n"
                "[bold green]2.[/bold green] Update Roblox Place ID\n"
                "[bold green]3.[/bold green] Adjust Launch Delay\n"
                "[bold green]4.[/bold green] Modify Grid Dimensions (Width/Height/X)\n"
                "[bold green]5.[/bold green] Update Discord Webhook URL\n"
                "[bold green]6.[/bold green] Toggle Auto Save Configuration\n"
                "[bold green]7.[/bold green] Modify Log Level Filter\n"
                "[bold green]8.[/bold green] Back to Main Menu"
            )
            console.print(Panel(menu_text, title="Configuration Submenu", border_style="bright_blue"))
            
            choice = Prompt.ask(
                "[bold magenta]Pilih setting yang ingin diubah (1-8)[/bold magenta]",
                choices=["1", "2", "3", "4", "5", "6", "7", "8"],
                default="8"
            )
            
            if choice == "1":
                new_pkg = Prompt.ask("[*] Masukkan nama package baru")
                self.config_mgr.set_value("package", new_pkg)
            elif choice == "2":
                new_pid = Prompt.ask("[*] Masukkan Roblox Place ID")
                self.config_mgr.set_value("place_id", new_pid)
            elif choice == "3":
                new_delay = Prompt.ask("[*] Durasi delay (detik)", default="20")
                self.config_mgr.set_value("launch_delay", int(new_delay))
            elif choice == "4":
                # SUB-MENU GRID
                console.print("[bold cyan]-- Modify Grid Dimensions --[/bold cyan]")
                self.config_mgr.config_data["grid_width"] = int(Prompt.ask("Lebar Window", default=str(self.config_mgr.config_data.get("grid_width", 280))))
                self.config_mgr.config_data["grid_height"] = int(Prompt.ask("Tinggi Window", default=str(self.config_mgr.config_data.get("grid_height", 200))))
                self.config_mgr.config_data["grid_start_x"] = int(Prompt.ask("Grid Start X", default=str(self.config_mgr.config_data.get("grid_start_x", 660))))
            elif choice == "5":
                new_webhook = Prompt.ask("[*] Tempel URL Discord Webhook")
                self.config_mgr.set_value("discord_webhook", new_webhook)
            elif choice == "6":
                new_autosave = Confirm.ask("[*] Aktifkan auto-save?")
                self.config_mgr.set_value("autosave", new_autosave)
            elif choice == "7":
                new_level = Prompt.ask("[*] Level logging", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
                self.config_mgr.set_value("log_level", new_level)
            elif choice == "8":
                break
            
            # Auto-save ke config.json setiap ada perubahan
            if hasattr(self.config_mgr, 'save_config'):
                self.config_mgr.save_config()
            
            console.print("[bold green][+] Perubahan konfigurasi berhasil direkam![/bold green]")
            time.sleep(1)
