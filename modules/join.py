"""
DHub-Rejoin - Premium KAERU Visual Engine (Fixed Structure & Dual Column Layout)
Author: Senior Python Developer
Description: Delivers a clean, multi-threaded, non-duplicating terminal status monitor.
"""

import time
import subprocess
import threading
import sys
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

class JoinManager:
    def __init__(self, config_mgr, logger):
        self.config_mgr = config_mgr
        self.logger = logger
        
        from modules.webhook import WebhookManager
        from modules.arrange import ArrangeManager
        
        self.webhook_mgr = WebhookManager(config_mgr, logger)
        self.arrange_mgr = ArrangeManager(config_mgr, logger)
        
        self.is_monitoring = False
        self.monitor_thread = None
        self.engine_status = "Ready"

    def _execute_shell(self, command: str) -> bool:
        try:
            root_command = f"su -c '{command}'"
            result = subprocess.run(root_command, shell=True, capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Root Execution error: {e}")
            return False

    def trigger_intent_launch(self, target_pkg: str, place_id: str):
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
        self.logger.info("Background logcat daemon monitoring loop activated.")
        self._execute_shell("logcat -c")
        
        self.engine_status = "Launched"
        self.trigger_intent_launch(target_pkg, place_id)
        self.engine_status = "Online"
        
        logcat_cmd = f"su -c 'logcat | grep -E \"{target_pkg}|ContentProvider|Disconnected|died|ActivityManager: Crashing\"'"
        
        try:
            process = subprocess.Popen(logcat_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            while self.is_monitoring:
                line = process.stdout.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                
                if any(kw in line for kw in ["died", "crash", "FORCE-CLOSE", "Disconnected", "ActivityManager: Process"]):
                    self.logger.warning(f"DC Event Detected: {line.strip()}")
                    self.webhook_mgr.send_status_embed(status="REJOINING", action_detail="DC detected by DHub Daemon.")
                    
                    self.engine_status = "Offline"
                    self._execute_shell(f"am force-stop {target_pkg}")
                    
                    for i in range(5, 0, -1):
                        self.engine_status = f"Cooldown ({i}s)"
                        time.sleep(1)
                        
                    self.engine_status = "Launched"
                    self.trigger_intent_launch(target_pkg, place_id)
                    
                    self._execute_shell("logcat -c")
                    self.engine_status = "Online"
                    
                time.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error within background daemon loop: {e}")
            self.engine_status = "Offline"
        finally:
            if process:
                process.terminate()

    def print_kaeru_layout(self, kaeru_header: str, target_pkg: str, place_id: str, ram_info: str):
        """Mencetak struktur tabel terbungkus kotak cyan yang stabil dan rapi (Anti-Hancur)."""
        # Bersihkan terminal secara instan ke koordinat awal 0,0
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()
        
        # Tampilkan logo teks besar DHUB di atas
        console.print(kaeru_header)
        
        # PEMBUATAN TABEL: Menggunakan border SQUARE solid cyan agar persis seperti KAERU
        table = Table(box=box.SQUARE, border_style="cyan", show_header=True, header_style="bold cyan", width=70)
        table.add_column("PACKAGE", style="bold white", width=42)
        table.add_column("STATUS", style="bold cyan", width=24)
        
        delay_cfg = self.config_mgr.config_data.get("launch_delay", 3)
        
        # 1. Baris Informasi System Memory
        table.add_row("System Memory", f"Free: {ram_info}")
        
        # 2. Baris Informasi Launch Delay
        table.add_row("Launch Delay", f"{delay_cfg}s...")
        
        # Baris kosong sebagai pembatas struktural tengah tabel
        table.add_section()
        
        # Penentuan warna status dinamis
        if self.engine_status == "Online":
            status_display = "[bold green]Online[/bold green]"
        elif self.engine_status == "Launched":
            status_display = "[bold yellow]Launched[/bold yellow]"
        elif self.engine_status == "Offline":
            status_display = "[bold red]Offline[/bold red]"
        else:
            status_display = f"[bold magenta]{self.engine_status}[/bold magenta]"
            
        # 3. Baris Target Package Aktif
        table.add_row(f"{target_pkg}", status_display)
        
        # Cetak objek tabel ke layar
        console.print(table)
        console.print("\n[dim white]» Tekan Enter Kapan Saja Untuk Berhenti Pemantauan Core Engine...[/dim white]")

    def launch_app(self):
        """Siklus utama peluncuran asinkron dengan visualisasi rendering terisolasi."""
        kaeru_header = (
            "[bold cyan]██████╗ ██╗  ██╗██╗   ██╗██████╗ \n"
            "██╔══██╗██║  ██║██║   ██║██╔══██╗\n"
            "██║  ██║███████║██║   ██║██████╔╝\n"
            "██║  ██║██╔══██║██║   ██║██╔══██╗\n"
            "██████╔╝██║  ██║╚██████╔╝██████╔╝\n"
            "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ [/bold cyan]\n"
            "            [bold white]Launcher v1.0[/bold white]\n"
        )
        
        target_pkg = self.config_mgr.config_data.get("package", "")
        place_id = self.config_mgr.config_data.get("place_id", "")
        
        if not target_pkg:
            console.clear()
            console.print("[bold red][!] ERROR: Paket target kosong! Jalankan Scan terlebih dahulu.[/bold red]")
            return

        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=1)

        self.is_monitoring = True
        self.engine_status = "Ready"
        
        self.monitor_thread = threading.Thread(
            target=self.background_monitor_loop,
            args=(target_pkg, place_id),
            daemon=True
        )
        self.monitor_thread.start()

        try:
            stop_event = threading.Event()
            
            def wait_for_user_exit():
                input()
                stop_event.set()
                
            input_thread = threading.Thread(target=wait_for_user_exit, daemon=True)
            input_thread.start()
            
            while not stop_event.is_set():
                self.print_kaeru_layout(kaeru_header, target_pkg, place_id, ram_info)
                time.sleep(0.5)
                
        finally:
            self.is_monitoring = False
            
        console.clear()
        console.print("[bold yellow][!] Pengawasan dinonaktifkan. Kembali ke panel utama...[/bold yellow]")
        time.sleep(1)
