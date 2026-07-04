"""
DHub-Rejoin - Application Joiner & Launcher Module (Deep Linking Support)
Author: Senior Python Developer
Description: Custom monitoring layout with automated Roblox Deep Link game injection capability.
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
        """
        Mengeksekusi perintah shell tingkat root/superuser.
        """
        try:
            root_command = f"su -c '{command}'"
            result = subprocess.run(root_command, shell=True, capture_output=True, text=True, timeout=15)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Root Execution error: {e}")
            return False

    def launch_app(self):
        """
        Meluncurkan clone aplikasi Roblox langsung meloncat ke game spesifik menggunakan Android Intent URI Scheme.
        """
        console.clear()
        
        kaeru_header = (
            "[bold cyan]██████╗ ██╗  ██╗██╗   ██╗██████╗ \n"
            "██╔══██╗██║  ██║██║   ██║██╔══██╗\n"
            "██║  ██║███████║██║   ██║██████╔╝\n"
            "██║  ██║██╔══██║██║   ██║██╔══██╗\n"
            "██████╔╝██║  ██║╚██████╔╝██████╔╝\n"
            "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ [/bold cyan]\n"
            "            [bold white]Launcher v1.0 (Deep-Link)[/bold white]\n"
        )
        console.print(kaeru_header)
        
        target_pkg = self.config_mgr.config_data.get("package", "")
        place_id = self.config_mgr.config_data.get("place_id", "")
        delay = self.config_mgr.config_data.get("launch_delay", 3)
        
        if not target_pkg:
            console.print("[bold red][!] ERROR: Paket target kosong! Jalankan Scan terlebih dahulu.[/bold red]")
            return

        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        # Visualisasi monitoring dashboard
        monitor_table = Table(box=None, padding=(0, 2))
        monitor_table.add_column("TARGET APP / CLONE", style="bold white", width=25)
        monitor_table.add_column("TARGET PLACE ID", style="bold yellow", width=18)
        monitor_table.add_column("SYSTEM RAM", style="bold cyan", width=15)
        monitor_table.add_column("ENGINE STATUS", style="bold green", width=15)
        
        display_pid = place_id if place_id else "Global Launch"
        monitor_table.add_row(target_pkg, display_pid, ram_info, "Monitoring...")
        
        console.print(Panel(monitor_table, border_style="cyan"))
        
        console.print(f"\n[bold yellow][*] Memulai hitung mundur stabilitas delay ({delay}s)...[/bold yellow]")
        time.sleep(delay)
        
        console.print("[bold green][*] Menembakkan Deep Link Intent Bypass via Root...[/bold green]")
        
        # LOGIKA BYPASS UTAMA:
        # Jika Place ID diatur di settings, kita paksa android membuka package tersebut 
        # langsung melompat ke server game yang dituju menggunakan skema URI data.
        if place_id:
            cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {target_pkg}"
            action_desc = f"Forced Auto-Rejoin directly to Place ID: {place_id}"
        else:
            # Fallback jika Place ID dikosongkan (Buka aplikasi normal)
            cmd = f"monkey -p {target_pkg} -c android.intent.category.LAUNCHER 1"
            action_desc = "Normal Global App Launch executed."
            
        success = self._execute_shell(cmd)
        
        if success:
            console.print("[bold green][+] Sukses! Perintah Rejoin berhasil dieksekusi langsung menuju target game.[/bold green]")
            self.webhook_mgr.send_status_embed(status="SUCCESS", action_detail=action_desc)
        else:
            console.print("[bold red][!] Gagal: Emulator menolak paket intent. Periksa kembali nama package / status root clone Anda.[/bold red]")
            self.webhook_mgr.send_status_embed(status="FAILED", action_detail=f"Failed to push view intent for Place ID {place_id}")
