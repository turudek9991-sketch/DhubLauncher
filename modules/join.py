"""
DHub-Rejoin - Premium KAERU Curses Visual Engine (Anti-Crash Edition)
Author: Senior Python Developer
Description: High-stability curses layout engineered specifically to run inside cloud emulators without triggering Android process kills.
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
                    time.sleep(1.0) # Ditambah jeda agar menghemat CPU dari overhead logcat
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
                    
                time.sleep(0.5) # Anti-Crash: Membatasi kecepatan loop background
        except Exception as e:
            self.logger.error(f"Error within background daemon loop: {e}")
            self.engine_status = "Offline"
        finally:
            if process:
                process.terminate()

    def print_kaeru_curses(self, stdscr, target_pkg: str, ram_info: str):
        """Merender UI kokoh bergaris dengan Logo DHUB besar menggunakan engine curses tingkat rendah."""
        stdscr.erase()
        
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        
        cyan = curses.color_pair(1)
        white = curses.color_pair(2)
        
        if self.engine_status == "Online":
            status_color = curses.color_pair(3) | curses.A_BOLD
        elif self.engine_status in ["Launched", "Ready"]:
            status_color = curses.color_pair(4) | curses.A_BOLD
        else:
            status_color = curses.color_pair(5) | curses.A_BOLD

        # Mengambil delay saat ini (jika tidak diatur, otomatis default ke 20 detik)
        delay_cfg = self.config_mgr.config_data.get("launch_delay", 20)
        
        # [KEMBALIKAN LOGO DHUB BESAR]: Menggunakan pencetakan berbasis koordinat baris absolut
        stdscr.addstr(0, 2, "██████╗ ██╗  ██╗██╗   ██╗██████╗", cyan | curses.A_BOLD)
        stdscr.addstr(1, 2, "██╔══██╗██║  ██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(2, 2, "██║  ██║███████║██║   ██║██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(3, 2, "██║  ██║██╔══██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(4, 2, "██████╔╝██║  ██║╚██████╔╝██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(5, 2, "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝   Launcher v1.0", cyan | curses.A_BOLD)
        
        # Geser posisi Tabel KAERU ke bawah agar tidak bertabrakan dengan logo (Mulai baris ke-7)
        stdscr.addstr(7, 0, "┌──────────────────────────────────────────┬────────────────────────┐", cyan)
        stdscr.addstr(8, 0, "│ PACKAGE                                  │ STATUS                 │", cyan)
        stdscr.addstr(8, 2, "PACKAGE", white | curses.A_BOLD)
        stdscr.addstr(8, 45, "STATUS", cyan | curses.A_BOLD)
        
        stdscr.addstr(9, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Baris System Memory
        stdscr.addstr(10, 0, "│ System Memory                            │                        │", cyan)
        stdscr.addstr(10, 45, f"Free: {ram_info}", white)
        
        # Baris Launch Delay
        stdscr.addstr(11, 0, "│ Launch Delay                             │                        │", cyan)
        stdscr.addstr(11, 45, f"{delay_cfg}s...", white)
        
        stdscr.addstr(12, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Baris Target Package Roblox
        display_pkg = target_pkg[:38] if len(target_pkg) > 38 else target_pkg
        stdscr.addstr(13, 0, "│                                          │                        │", cyan)
        stdscr.addstr(13, 2, display_pkg, white)
        stdscr.addstr(13, 45, self.engine_status, status_color)
        
        stdscr.addstr(14, 0, "└──────────────────────────────────────────┴────────────────────────┘", cyan)
        
        stdscr.addstr(16, 0, "» Tekan 'q' atau 'Enter' untuk berhenti dan kembali ke menu...", white | curses.A_DIM)
        
        stdscr.refresh()

    def launch_app(self):
        """Titik masuk siklus monitoring terisolasi menggunakan curses wrapper dengan optimasi stabilitas CPU."""
        target_pkg = self.config_mgr.config_data.get("package", "")
        place_id = self.config_mgr.config_data.get("place_id", "")
        
        if not target_pkg:
            os.system("clear")
            print("\033[91m[!] ERROR: Paket target kosong! Jalankan Scan terlebih dahulu.\033[0m")
            return

        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        # [FORCED DEFAULT DELAY TO 20]: Memastikan jika konfigurasi di bawah 20 atau kosong, di-set ke 20
        current_delay = self.config_mgr.config_data.get("launch_delay", 3)
        if current_delay < 20:
            self.config_mgr.set_value("launch_delay", 20)

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

        def curses_main(stdscr):
            curses.curs_set(0)
            # Mengubah waktu blocking timeout menjadi lebih santai (500ms) demi mencegah Termux di-kill Android
            stdscr.nodelay(True)
            stdscr.timeout(500)
            
            while self.is_monitoring:
                self.print_kaeru_curses(stdscr, target_pkg, ram_info)
                
                try:
                    key = stdscr.getch()
                    if key in [ord('q'), ord('Q'), 10]: # Deteksi tombol keluar
                        break
                except Exception:
                    pass
                    
                # [ANTI-CRASH PIVOTAL]: Memberikan napas yang cukup bagi CPU tty terminal
                time.sleep(0.5)

        try:
            curses.wrapper(curses_main)
        finally:
            self.is_monitoring = False
            
        os.system("clear")
        print("\033[93m[!] Pengawasan dinonaktifkan. Kembali ke panel utama...\033[0m")
        time.sleep(1)
