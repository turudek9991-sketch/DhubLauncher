"""
DHub-Rejoin - Automated Daemon Monitor & Asynchronous Launcher
Author: Senior Python Developer
Description: Features continuous background logcat inspection for DC detection without freezing the CLI.
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
        """Daemon Worker: Memantau logcat perangkat untuk mendeteksi Crash/DC secara real-time."""
        self.logger.info("Background logcat daemon monitoring loop activated.")
        
        # Bersihkan logcat lama agar tidak mendeteksi error masa lalu
        self._execute_shell("logcat -c")
        
        # Pemicu awal masuk game
        self.trigger_intent_launch(target_pkg, place_id)
        
        # Jalankan proses pembacaan stream logcat Android
        # Memantau tanda-tanda disconnection, error link, pembersihan memori, atau penghentian paksa
        logcat_cmd = f"su -c 'logcat | grep -E \"{target_pkg}|ContentProvider|Disconnected|died|ActivityManager: Crashing\"'"
        
        try:
            process = subprocess.Popen(logcat_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while self.is_monitoring:
                line = process.stdout.readline()
                if not line:
                    time.sleep(1)
                    continue
                
                # Deteksi pola kegagalan koneksi atau force close
                # Kata kunci sensitif untuk roblox/clones terputus dari server
                if any(kw in line for kw in ["died", "crash", "FORCE-CLOSE", "Disconnected", "ActivityManager: Process"]):
                    self.logger.warning(f"DC Event Detected in logcat stream: {line.strip()}")
                    self.webhook_mgr.send_status_embed(status="REJOINING", action_detail="Network Disconnection / App Crash detected by DHub Daemon.")
                    
                    # Berikan jeda 5 detik untuk cooldown pembersihan memori sistem
                    self._execute_shell(f"am force-stop {target_pkg}")
                    time.sleep(5)
                    
                    # Pemicu masuk kembali secara paksa ke game target
                    self.trigger_intent_launch(target_pkg, place_id)
                    self._execute_shell("logcat -c") # Reset kembali buffer logcat
                    
                time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error within background daemon monitor loop: {e}")
        finally:
            if process:
                process.terminate()

    def generate_dashboard_table(self, target_pkg: str, place_id: str, ram_info: str, status_text: str) -> Table:
        """Membuat objek komponen tabel visual untuk rendering dinamis."""
        monitor_table = Table(box=None, padding=(0, 2))
        monitor_table.add_column("TARGET APP / CLONE", style="bold white", width=25)
        monitor_table.add_column("TARGET PLACE ID", style="bold yellow", width=18)
        monitor_table.add_column("SYSTEM RAM", style="bold cyan", width=15)
        monitor_table.add_column("ENGINE STATUS", style="bold green", width=20)
        
        display_pid = place_id if place_id else "Global Launch"
        monitor_table.add_row(target_pkg, display_pid, ram_info, status_text)
        return monitor_table

    def launch_app(self):
        """Meluncurkan proses monitoring asinkron tanpa mengunci antarmuka terminal utama."""
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

        # Jika daemon sedang berjalan, matikan terlebih dahulu untuk mencegah kebocoran memori thread
        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)

        # Aktifkan flag pengawas
        self.is_monitoring = True
        
        # Membuka Thread baru di latar belakang agar antarmuka termux tidak membeku (Anti-Freeze)
        self.monitor_thread = threading.Thread(
            target=self.background_monitor_loop,
            args=(target_pkg, place_id),
            daemon=True
        )
        self.monitor_thread.start()

        # Gunakan Rich Live display untuk memantau visual tanpa merusak terminal
        with Live(self.generate_dashboard_table(target_pkg, place_id, ram_info, "[bold green]Active Monitoring[/bold green]"), refresh_per_second=1) as live:
            console.print(f"\n[bold green][+] Engine DHub Berhasil Berjalan di Latar Belakang! [/bold green]")
            console.print("[yellow][*] Perangkat lunak sedang mengawasi tanda-tanda putus koneksi (DC) game Anda...[/yellow]")
            console.print("[dim white][*] Tekan Enter Kapan Saja Untuk Menghentikan Pengawasan Core Engine.[/dim white]")
            
            # Menunggu input masukan pengguna secara aman tanpa nge-freeze sistem
            input()
            
            # Jika user menekan enter, hentikan sistem monitoring daemon background
            self.is_monitoring = False
            live.update(self.generate_dashboard_table(target_pkg, place_id, ram_info, "[bold red]Stopped[/bold red]"))
            
        console.print("[bold yellow][!] Pengawasan dihentikan. Kembali ke panel kendali utama...[/bold yellow]")
        time.sleep(1.5)
