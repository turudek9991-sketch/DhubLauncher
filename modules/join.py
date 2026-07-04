"""
DHub-Rejoin - Application Joiner & Launcher Module (KAERU Visual Style)
Author: Senior Python Developer
Description: Custom monitoring layout mimicking premium automated instance dashboards.
"""

import time
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from modules.webhook import WebhookManager
from modules.arrange import ArrangeManager

console = Console()

class JoinManager:
    def __init__(self, config_mgr, logger):
        self.config_mgr = config_mgr
        self.logger = logger
        self.webhook_mgr = WebhookManager(config_mgr, logger)
        self.arrange_mgr = ArrangeManager(config_mgr, logger)

    def _execute_shell(self, command: str) -> bool:
        try:
            root_command = f"su -c '{command}'"
            result = subprocess.run(root_command, shell=True, capture_output=True, text=True, timeout=15)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Root Execution error: {e}")
            return False

    def launch_app(self):
        """
        Meluncurkan aplikasi dengan visualisasi dashboard terpusat layaknya tool bypass premium.
        """
        console.clear()
        
        # Header Teks Besar Sesuai Permintaan
        kaeru_header = (
            "[bold cyan]██████╗ ██╗  ██╗██╗   ██╗██████╗ \n"
            "██╔══██╗██║  ██║██║   ██║██╔══██╗\n"
            "██║  ██║███████║██║   ██║██████╔╝\n"
            "██║  ██║██╔══██║██║   ██║██╔══██╗\n"
            "██████╔╝██║  ██║╚██████╔╝██████╔╝\n"
            "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ [/bold cyan]\n"
            "            [bold white]Launcher v1.0[/bold white]\n"
        )
        console.print(kaeru_header)
        
        target_pkg = self.config_mgr.config_data.get("package", "")
        delay = self.config_mgr.config_data.get("launch_delay", 3)
        
        if not target_pkg:
            console.print("[bold red][!] ERROR: Paket target kosong! Jalankan Scan terlebih dahulu.[/bold red]")
            return

        # Mendapatkan info RAM/System Memory real-time untuk diletakkan di samping tabel
        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        # Kontruksi Tabel Mirip Gambar KAERU
        monitor_table = Table(box=None, padding=(0, 2))
        monitor_table.add_column("PACKAGE", style="bold white", width=30)
        monitor_table.add_column("SYSTEM MEMORY", style="bold cyan", width=20)
        monitor_table.add_column("STATUS", style="bold cyan", width=15)
        
        # Baris data utama
        monitor_table.add_row(target_pkg, f"Free RAM:", "[bold green]Online[/bold green]")
        monitor_table.add_row("(w1dnFarmer...)", ram_info, "[bold green]Online[/bold green]")
        
        console.print(Panel(monitor_table, border_style="cyan"))
        
        console.print(f"\n[bold yellow][*] Memulai hitung mundur stabilitas delay ({delay}s)...[/bold yellow]")
        time.sleep(delay)
        
        console.print("[bold green][*] Mengirimkan trigger Superuser Intent Launch...[/bold green]")
        cmd = f"monkey -p {target_pkg} -c android.intent.category.LAUNCHER 1"
        
        success = self._execute_shell(cmd)
        
        if success:
            console.print("[bold green][+] Aplikasi berhasil diluncurkan! Sistem otomasi berjalan di latar belakang.[/bold green]")
            self.webhook_mgr.send_status_embed(status="SUCCESS", action_detail=f"Automated Rejoin for {target_pkg} executed successfully.")
        else:
            console.print("[bold red][!] Akses intent gagal didorong. Pastikan emulator memberikan izin root penuh ke Termux.[/bold red]")
