"""
DHub-Rejoin - Utilities Module
Author: Senior Python Developer
Description: Provides core auxiliary functions such as log inspection directly inside the terminal.
"""

import os
import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()

class UtilsManager:
    def __init__(self, config_mgr, logger):
        """
        Inisialisasi UtilsManager dengan konfigurasi dan logger.
        """
        self.config_mgr = config_mgr
        self.logger = logger

    def view_logs(self):
        """
        Membaca file log hari ini berdasarkan format tanggal dinamis dan menampilkannya di terminal.
        """
        console.clear()
        console.print(Panel("[bold yellow]APPLICATION LOG VIEWER[/bold yellow]", border_style="yellow"))
        
        # Ambil tanggal hari ini untuk mencocokkan nama file log (Format: YYYY-MM-DD)
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        log_filename = f"logs/{today_str}.log"
        
        if not os.path.exists(log_filename):
            console.print(f"[bold red][!] File log untuk hari ini ({log_filename}) belum terbentuk atau kosong.[/bold red]")
            return
            
        console.print(f"[green][*] Membaca catatan aktivitas dari file Log: [yellow]{log_filename}[/yellow]\n")
        
        try:
            with open(log_filename, "r", encoding="utf-8") as f:
                log_content = f.read()
                
            if not log_content.strip():
                console.print("[dim white]File log kosong.[/dim white]")
            else:
                # Bungkus log dalam Rich Panel dengan border redup agar terkesan bersih
                console.print(Panel(
                    log_content, 
                    title=f"Log Data stream - {today_str}", 
                    border_style="dim white",
                    expand=True
                ))
                
            self.logger.info("Log history successfully displayed on terminal screen.")
        except Exception as e:
            console.print(f"[bold red][!] Gagal membaca file log: {e}[/bold red]")
            self.logger.error(f"Failed to read log stream payload: {e}")
