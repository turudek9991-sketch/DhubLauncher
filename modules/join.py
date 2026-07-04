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

console = Console()

class JoinManager:
    def __init__(self, config_mgr, logger):
        self.config_mgr = config_mgr
        self.logger = logger
        
        # Penanganan impor lokal yang aman untuk menghindari circular dependency
        from modules.webhook import WebhookManager
        from modules.arrange import ArrangeManager
        
        self.webhook_mgr = WebhookManager(config_mgr, logger)
        self.arrange_mgr = ArrangeManager(config_mgr, logger)
        
        self.is_monitoring = False
        self.monitor_thread = None
        self.engine_status = "Ready"

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
        """Mencetak struktur tabel dua kolom murni secara manual dan membersihkan layar terminal."""
        # Gunakan ANSI Escape Code untuk membersihkan layar secara instan dan efisien (Anti-Duplikasi)
        sys.stdout.write("\033[H\033[2J")
        sys.stdout.flush()
        
        # Cetak Header Besar di Pucuk
        console.print(kaeru_header)
        
        # Buat Struktur Tabel Dua Kolom Murni Sesuai Gambar Referensi
        table = Table(box=None, padding=(0, 4), show_header=True, header_style="bold cyan")
        table.add_column("PACKAGE", style="bold white", width=42)
        table.add_column("STATUS", style="bold cyan", width=24)
        
        # Ambil delay konfigurasi saat ini
        delay_cfg = self.config_mgr.config_data.get("launch_delay", 3)
        
        # Baris 1: Informasi Sistem Memori (RAM)
        table.add_row("System Memory", f"Free: {ram_info}")
        
        # Baris 2: Informasi Delay Aktif
        table.add_row("Launch Delay", f"{delay_cfg}s...")
        
        # Baris Pembatas Horizontal Kustom
        table.add_row("─" * 42, "─" * 24)
        
        # Pewarnaan Status Dinamis
        status_display = f"[bold green]{self.engine_status}[/bold green]" if self.engine_status in ["Online", "Launched"] else f"[bold magenta]{self.engine_status}[/bold magenta]"
        if self.engine_status == "Offline":
            status_display = "[bold red]Offline[/bold red]"
        elif self.engine_status == "Ready":
            status_display = "[white]Ready[/white]"
            
        # Baris 3: Informasi Target Package
        # Catatan: Jika ingin menyuntikkan teks username khusus seperti (w1dnFarmer), Anda tinggal menambahkannya di parameter string di bawah
        table.add_row(f"{target_pkg}", status_display)
        
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
        
        # Membuka thread latar belakang
        self.monitor_thread = threading.Thread(
            target=self.background_monitor_loop,
            args=(target_pkg, place_id),
            daemon=True
        )
        self.monitor_thread.start()

        # Engine loop rendering manual (Anti-Freeze & Anti-Duplicate)
        # Mengeliminasi component Live rich agar kompatibel penuh dengan lingkungan termux cloud
        try:
            # Thread pembantu untuk menangani interaksi stop input non-blocking
            stop_event = threading.Event()
            
            def wait_for_user_exit():
                input()
                stop_event.set()
                
            input_thread = threading.Thread(target=wait_for_user_exit, daemon=True)
            input_thread.start()
            
            while not stop_event.is_set():
                # Render ulang data secara bersih di baris konsol yang sama
                self.print_kaeru_layout(kaeru_header, target_pkg, place_id, ram_info)
                time.sleep(0.5)
                
        finally:
            self.is_monitoring = False
            
        console.clear()
        console.print("[bold yellow][!] Pengawasan dinonaktifkan. Kembali ke panel utama...[/bold yellow]")
        time.sleep(1)
