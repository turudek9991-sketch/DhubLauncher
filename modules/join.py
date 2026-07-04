"""
DHub-Rejoin - Automated Daemon Monitor & Asynchronous Launcher (KAERU Pure Visual)
Author: Senior Python Developer
Description: High-performance background logcat monitoring with unified table status reporting.
"""

import time
import subprocess
import threading
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from modules.webhook import WebhookManager
from modules.arrange import ArrangeManager

console = Console()

class JoinManager:
    def __init__(self, config_mgr, logger):
        self.config_mgr = config_mgr
        self.logger = logger
        self.webhook_mgr = WebhookManager(config_mgr, logger)
        self.arrange_mgr = ArrangeManager(config_mgr, logger)
        
        # Flag kontrol untuk thread pemantauan
        self.is_monitoring = False
        self.monitor_thread = None
        # Variabel penampung status dinamis untuk tabel
        self.engine_status = "[bold yellow]Initializing...[/bold yellow]"

    def _execute_shell(self, command: str) -> bool:
        """Eksekusi perintah internal dengan hak akses superuser root."""
        try:
            root_command = f"su -c '{command}'"
            result = subprocess.run(root_command, shell=True, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Root Execution error: {e}")
            return False

    def trigger_intent_launch(self, target_pkg: str, place_id: str):
        """Menembakkan Android Intent URI Scheme langsung menuju target game."""
        if place_id:
            cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {target_pkg}"
            action_desc = f"Auto-Rejoin fired directly to Place ID: {place_id}"
        else:
            cmd = f"monkey -p {target_pkg} -c android.intent.category.LAUNCHER 1"
            action_desc = "Global App Launch fired."

        success = self._execute_shell(cmd)
        if success:
            self.logger.info(f"Intent successfully pushed: {action_desc}")
            self.webhook_mgr.send_status_embed(status="SUCCESS", action_detail=action_desc)
        else:
            self.logger.error("Failed to push root intent.")
            self.webhook_mgr.send_status_embed(status="FAILED", action_detail="Failed to push root intent during daemon cycle.")

    def background_monitor_loop(self, target_pkg: str, place_id: str):
        """Daemon Worker: Memantau logcat perangkat untuk mendeteksi Crash/DC di latar belakang."""
        self.logger.info("Background logcat daemon monitoring loop activated.")
        
        # Bersihkan logcat lama agar tidak mendeteksi error masa lalu
        self._execute_shell("logcat -c")
        
        # Pemicu awal masuk game
        self.engine_status = "[bold green]Launching Game...[/bold green]"
        self.trigger_intent_launch(target_pkg, place_id)
        
        # Set status ke mode mengawasi aktif
        self.engine_status = "[bold green]Active Monitoring[/bold green]"
        
        logcat_cmd = f"su -c 'logcat | grep -E \"{target_pkg}|ContentProvider|Disconnected|died|ActivityManager: Crashing\"'"
        
        try:
            process = subprocess.Popen(logcat_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while self.is_monitoring:
                line = process.stdout.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                
                # Deteksi pola kegagalan koneksi atau force close
                if any(kw in line for kw in ["died", "crash", "FORCE-CLOSE", "Disconnected", "ActivityManager: Process"]):
                    self.logger.warning(f"DC Event Detected in logcat stream: {line.strip()}")
                    self.engine_status = "[bold red]DC Detected! Rejoining...[/bold red]"
                    
                    self.webhook_mgr.send_status_embed(status="REJOINING", action_detail="Network Disconnection / App Crash detected by DHub Daemon.")
                    
                    # Eksekusi pembersihan & force stop aplikasi
                    self._execute_shell(f"am force-stop {target_pkg}")
                    
                    # Cooldown 5 detik, status di-update di tabel
                    for i in range(5, 0, -1):
                        self.engine_status = f"[bold magenta]Cooldown ({i}s)...[/bold magenta]"
                        time.sleep(1)
                        
                    self.engine_status = "[bold cyan]Injecting Intent...[/bold cyan]"
                    self.trigger_intent_launch(target_pkg, place_id)
                    
                    # Reset buffer logcat dan kembalikan ke monitoring aktif
                    self._execute_shell("logcat -c")
                    self.engine_status = "[bold green]Active Monitoring[/bold green]"
                    
                time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error within background daemon monitor loop: {e}")
            self.engine_status = "[bold red]Daemon Error[/bold red]"
        finally:
            if process:
                process.terminate()

    def generate_dashboard_table(self, target_pkg: str, place_id: str, ram_info: str) -> Table:
        """Membuat objek komponen tabel visual untuk rendering dinamis tanpa log numpuk."""
        monitor_table = Table(box=None, padding=(0, 2))
        monitor_table.add_column("TARGET APP / CLONE", style="bold white", width=25)
        monitor_table.add_column("TARGET PLACE ID", style="bold yellow", width=18)
        monitor_table.add_column("SYSTEM RAM", style="bold cyan", width=15)
        monitor_table.add_column("ENGINE STATUS", style="bold green", width=25)
        
        display_pid = place_id if place_id else "Global Launch"
        monitor_table.add_row(target_pkg, display_pid, ram_info, self.engine_status)
        return monitor_table

    def launch_app(self):
        """Meluncurkan proses monitoring asinkron dengan visualisasi tabel tunggal yang bersih."""
        console.clear()
        
        kaeru_header = (
            "[bold cyan]██████╗ ██╗  ██╗██╗   ██╗██████╗ \n"
            "██╔══██╗██║  ██║██║   ██║██╔══██╗\n"
            "██║  ██║███████║██║   ██║██████╔╝\n"
            "██║  ██║██╔══██║██║   ██║██╔══██╗\n"
            "██████╔╝██║  ██║╚██████╔╝██████╔╝\n"
            "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ [/bold cyan]\n"
            "            [bold white]Launcher v1.0 (Bypass Mode)[/bold white]\n"
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

        # Manajemen siklus thread daemon yang aman
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=1)

        self.is_monitoring = True
        self.engine_status = f"[bold yellow]Delay Counter ({delay}s)...[/bold yellow]"
        
        # Membuka Thread baru di latar belakang agar antarmuka termux tidak membeku (Anti-Freeze)
        self.monitor_thread = threading.Thread(
            target=self.background_monitor_loop,
            args=(target_pkg, place_id),
            daemon=True
        )
        self.monitor_thread.start()

        # Gunakan Rich Live display untuk memantau visual secara statis (Log tidak akan nge-print di bawahnya)
        with Live(self.generate_dashboard_table(target_pkg, place_id, ram_info), refresh_per_second=2) as live:
            # Loop pembaruan visual tabel secara berkala tanpa merusak baris terminal bawah
            while self.is_monitoring:
                live.update(self.generate_dashboard_table(target_pkg, place_id, ram_info))
                
                # Trick bypass input non-blocking: periksa apakah user menekan enter di thread utama shell
                # Namun karena kita ingin interaksi manual untuk keluar menu, kita biarkan loop berjalan 
                # Dan membaca flag kontrol utama.
                time.sleep(0.5)
                
            live.update(self.generate_dashboard_table(target_pkg, place_id, ram_info))

        console.print("[bold yellow][!] Pengawasan dihentikan. Kembali ke panel kendali utama...[/bold yellow]")
        time.sleep(1)
