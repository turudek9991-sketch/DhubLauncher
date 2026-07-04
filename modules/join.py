"""
DHub-Rejoin - Premium KAERU Curses Visual Engine
Author: Senior Python Developer
Description: Uses the standard python curses library to lock the terminal window dimensions, 
             preventing ANY layout shattering or flickering when switching apps.
"""

import time
import subprocess
import threading
import os
import curses

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

    def print_kaeru_curses(self, stdscr, target_pkg: str, ram_info: str):
        """Merender UI kokoh bergaris mirip KAERU menggunakan engine curses tingkat rendah."""
        # Bersihkan window curses internal secara total
        stdscr.erase()
        
        # Inisialisasi warna dasar jika didukung terminal
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        
        cyan = curses.color_pair(1)
        white = curses.color_pair(2)
        
        # Pilih warna berdasarkan status saat ini
        if self.engine_status == "Online":
            status_color = curses.color_pair(3) | curses.A_BOLD
        elif self.engine_status in ["Launched", "Ready"]:
            status_color = curses.color_pair(4) | curses.A_BOLD
        else:
            status_color = curses.color_pair(5) | curses.A_BOLD

        delay_cfg = self.config_mgr.config_data.get("launch_delay", 3)
        
        # Judul Atas
        stdscr.addstr(0, 2, "=== DHUB AUTOMATION LAUNCHER ===", cyan | curses.A_BOLD)
        
        # Render Tabel Garis Kotak Khas KAERU
        stdscr.addstr(2, 0, "┌──────────────────────────────────────────┬────────────────────────┐", cyan)
        stdscr.addstr(3, 0, "│ PACKAGE                                  │ STATUS                 │", cyan)
        stdscr.addstr(3, 2, "PACKAGE", white | curses.A_BOLD)
        stdscr.addstr(3, 45, "STATUS", cyan | curses.A_BOLD)
        
        stdscr.addstr(4, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Baris System Memory
        stdscr.addstr(5, 0, "│ System Memory                            │                        │", cyan)
        stdscr.addstr(5, 45, f"Free: {ram_info}", white)
        
        # Baris Launch Delay
        stdscr.addstr(6, 0, "│ Launch Delay                             │                        │", cyan)
        stdscr.addstr(6, 45, f"{delay_cfg}s...", white)
        
        stdscr.addstr(7, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Baris Data Akun Clone / Package target
        display_pkg = target_pkg[:38] if len(target_pkg) > 38 else target_pkg
        stdscr.addstr(8, 0, "│                                          │                        │", cyan)
        stdscr.addstr(8, 2, display_pkg, white)
        stdscr.addstr(8, 45, self.engine_status, status_color)
        
        stdscr.addstr(9, 0, "└──────────────────────────────────────────┴────────────────────────┘", cyan)
        
        stdscr.addstr(11, 0, "» Tekan 'q' untuk keluar dari mode monitoring...", white | curses.A_DIM)
        
        # Refresh screen fisik secara realtime
        stdscr.refresh()

    def launch_app(self):
        """Titik masuk siklus monitoring terisolasi menggunakan curses wrapper."""
        target_pkg = self.config_mgr.config_data.get("package", "")
        place_id = self.config_mgr.config_data.get("place_id", "")
        
        if not target_pkg:
            os.system("clear")
            print("\033[91m[!] ERROR: Paket target kosong! Jalankan Scan terlebih dahulu.\033[0m")
            return

        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        if self.is_monitoring:
            self.is_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=1)

        self.is_monitoring = True
        self.engine_status = "Ready"
        
        # Jalankan daemon pengecekan logcat di latar belakang
        self.monitor_thread = threading.Thread(
            target=self.background_monitor_loop,
            args=(target_pkg, place_id),
            daemon=True
        )
        self.monitor_thread.start()

        # Panggil curses wrapper utama agar terminal masuk ke mode grafis terkunci
        def curses_main(stdscr):
            # Hilangkan kedipan kursor terminal asli
            curses.curs_set(0)
            # Set deteksi input menjadi non-blocking agar perulangan visual tidak macet
            stdscr.nodelay(True)
            stdscr.timeout(100)
            
            while self.is_monitoring:
                self.print_kaeru_curses(stdscr, target_pkg, ram_info)
                
                # Cek apakah pengguna menekan tombol 'q' untuk keluar
                try:
                    key = stdscr.getch()
                    if key == ord('q') or key == ord('Q') or key == 10: # 10 adalah kode enter
                        break
                except Exception:
                    pass
                    
                time.sleep(0.5)

        try:
            curses.wrapper(curses_main)
        finally:
            self.is_monitoring = False
            
        os.system("clear")
        print("\033[93m[!] Pengawasan dinonaktifkan. Kembali ke panel utama...\033[0m")
        time.sleep(1)
