"""
DHub-Rejoin - Settings Management Module
Author: Senior Python Developer
Description: Provides interactive submenus to update application configurations dynamically.
"""

import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

console = Console()

class SettingsManager:
    def __init__(self, config_mgr, logger):
        """
        Inisialisasi SettingsManager dengan manajemen konfigurasi global dan logger.
        """
        self.config_mgr = config_mgr
        self.logger = logger

    def display_current_settings(self):
        """
        Menampilkan tabel konfigurasi terkini agar pengguna tahu parameter yang aktif.
        """
        table = Table(title="Current Configuration Settings", header_style="bold cyan")
        table.add_column("Setting Key", style="yellow")
        table.add_column("Value", style="white")
        
        cfg = self.config_mgr.config_data
        table.add_row("Application Package", str(cfg.get("package", "Not Set")))
        table.add_row("Launch Delay (seconds)", str(cfg.get("launch_delay", 3)))
        table.add_row("Theme", str(cfg.get("theme", "dark")))
        table.add_row("Discord Webhook URL", str(cfg.get("discord_webhook", "Not Set")))
        table.add_row("Auto Save Config", str(cfg.get("autosave", True)))
        table.add_row("Log Level", str(cfg.get("log_level", "INFO")))
        
        console.print(table)

    def open_settings(self):
        """
        Loop internal untuk mengelola Submenu Settings.
        """
        while True:
            console.clear()
            console.print(Panel("[bold yellow]SETTINGS CONFIGURATION PANEL[/bold yellow]", border_style="yellow"))
            self.display_current_settings()
            
            menu_text = (
                "[bold green]1.[/bold green] Change Application Package Target\n"
                "[bold green]2.[/bold green] Adjust Launch Delay\n"
                "[bold green]3.[/bold green] Switch Theme Style\n"
                "[bold green]4.[/bold green] Update Discord Webhook URL\n"
                "[bold green]5.[/bold green] Toggle Auto Save Configuration\n"
                "[bold green]6.[/bold green] Modify Log Level Filter\n"
                "[bold green]7.[/bold green] Back to Main Menu"
            )
            console.print(Panel(menu_text, title="Configuration Submenu", border_style="bright_blue"))
            
            choice = Prompt.ask(
                "[bold magenta]Pilih setting yang ingin diubah (1-7)[/bold magenta]",
                choices=["1", "2", "3", "4", "5", "6", "7"],
                default="7"
            )
            
            if choice == "1":
                new_pkg = Prompt.ask("[*] Masukkan nama package baru (e.g. com.roblox.client)")
                self.config_mgr.set_value("package", new_pkg)
                self.logger.info(f"Settings update: package={new_pkg}")
                
            elif choice == "2":
                new_delay = Prompt.ask("[*] Masukkan durasi penundaan launch (detik)", default="3")
                if new_delay.isdigit():
                    self.config_mgr.set_value("launch_delay", int(new_delay))
                    self.logger.info(f"Settings update: launch_delay={new_delay}")
                else:
                    console.print("[red][!] Input harus berupa angka valid.[/red]")
                    input("\nTekan Enter...")
                    
            elif choice == "3":
                new_theme = Prompt.ask("[*] Masukkan tema baru", choices=["dark", "light", "matrix"], default="dark")
                self.config_mgr.set_value("theme", new_theme)
                self.logger.info(f"Settings update: theme={new_theme}")
                
            elif choice == "4":
                new_webhook = Prompt.ask("[*] Tempel URL Discord Webhook baru")
                self.config_mgr.set_value("discord_webhook", new_webhook)
                self.logger.info("Settings update: discord_webhook token changed")
                
            elif choice == "5":
                new_autosave = Confirm.ask("[*] Aktifkan fitur otomatis simpan konfigurasi?")
                self.config_mgr.set_value("autosave", new_autosave)
                self.logger.info(f"Settings update: autosave={new_autosave}")
                
            elif choice == "6":
                new_level = Prompt.ask("[*] Pilih level logging", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
                self.config_mgr.set_value("log_level", new_level)
                self.logger.info(f"Settings update: log_level={new_level}")
                
            elif choice == "7":
                self.logger.info("Exiting Settings menu sub-loop")
                break
            
            # Konfirmasi penyimpanan
            console.print("[bold green][+] Perubahan konfigurasi berhasil direkam![/bold green]")
            input("\nTekan Enter untuk merefresh halaman pengaturan...")
