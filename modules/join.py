"""
DHub-Rejoin - Ultra Stability KAERU Visual Engine (Pure Text Layout - Anti-Shatter)
Author: Senior Python Developer
Description: Uses pure string formatting instead of rich.table to completely prevent layout breakdown when app goes to background.
"""

import time
import subprocess
import threading
import sys
from rich.console import Console

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
        """Mencetak layout KAERU menggunakan struktur teks kaku tanpa library tabel (Anti-Hancur)."""
        # Kembalikan posisi kursor ke baris paling atas (0,0) secara instan
        sys.stdout.write("\033[H")
        sys.stdout.flush()
        
        # Cetak logo teks besar DHUB
        console.print(kaeru_header)
        
        delay_cfg = self.config_mgr.config_data.get("launch_delay", 3)
        
        # Penentuan status warna murni teks
        if self.engine_status == "Online":
            status_display = "[bold green]Online[/bold green]"
        elif self.engine_status == "Launched":
            status_display = "[bold yellow]Launched[/bold yellow]"
        elif self.engine_status == "Offline":
            status_display = "[bold red]Offline[/bold red]"
        else:
            status_display = f"[bold magenta]{self.engine_status}[/bold magenta]"

        # KONSTRUKSI STRUKTUR TABEL MURNI TEKS (Kaku, Presisi, Mengunci Batas Kolom)
        # Lebar judul dikunci menggunakan format spasi manual agar tidak terpengaruh penyusutan layar terminal
        lines = [
            "[cyan]┌──────────────────────────────────────────┬────────────────────────┐[/cyan]",
            "[cyan]│[/cyan] [bold white]PACKAGE[/bold white]                                   [cyan]│[/cyan] [bold cyan]STATUS[/bold cyan]                 [cyan]│[/cyan]",
            "[cyan]├──────────────────────────────────────────┼────────────────────────┤[/cyan]",
            f"[cyan]│[/cyan] System Memory                             [cyan]│[/cyan] Free: {ram_info:<17} [cyan]│[/cyan]",
            f"[cyan]│[/cyan] Launch Delay                              [cyan]│[/cyan] {str(delay_cfg)+'s...':<17} [cyan]│[/cyan]",
            "[cyan]├──────────────────────────────────────────┼────────────────────────┤[/cyan]",
            f"[cyan]│[/cyan] {target_pkg:<40} [cyan]│[/cyan] {status_display:<26} [cyan]│[/cyan]",
            "[cyan]└──────────────────────────────────────────┴────────────────────────┘[/cyan]"
        ]
        
        # Cetak seluruh susunan teks kaku ke terminal
        for line in lines:
            console.print(line)
            
        console.print("\n[dim white]» Tekan Enter Kapan Saja Untuk Berhenti Pemantauan Core Engine...[/dim white]")

    def launch_app(self):
        """Siklus pemantauan dengan isolasi screen buffer penuh."""
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

        # AKTIFKAN ALTERNATE SCREEN BUFFER & SEMBUNYIKAN KURSOR
        sys.stdout.write("\033[?1049h\033[?25l")
        sys.stdout.flush()

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
            
            console.clear()
            
            while not stop_event.is_set():
                self.print_kaeru_layout(kaeru_header, target_pkg, place_id, ram_info)
                time.sleep(0.5)
                
        finally:
            self.is_monitoring = False
            # MATIKAN ALTERNATE SCREEN BUFFER & TAMPILKAN KURSOR KEMBALI
            sys.stdout.write("\033[?25h\033[?1049l")
            sys.stdout.flush()
            
        console.clear()
        console.print("[bold yellow][!] Pengawasan dinonaktifkan. Kembali ke panel utama...[/bold yellow]")
        time.sleep(1)
