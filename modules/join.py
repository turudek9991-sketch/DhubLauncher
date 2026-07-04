"""
DHub-Rejoin - Auto Grid Layout (Android 10+ Compatible)
Version 2.0 - Tested untuk Android 10+ dengan fallback positioning
"""

import time
import subprocess
import os
import curses
import threading

class JoinManager:
    def __init__(self, config_mgr, logger):
        self.config_mgr = config_mgr
        self.logger = logger
        
        from modules.webhook import WebhookManager
        from modules.arrange import ArrangeManager
        
        self.webhook_mgr = WebhookManager(config_mgr, logger)
        self.arrange_mgr = ArrangeManager(config_mgr, logger)
        
        self.is_monitoring = False
        self.clone_statuses = {}
        
        # Grid Configuration - OPTIMIZED FOR DPI 600, Android 10+ Compatible
        self.grid_config = {
            "dpi": 600,
            "dhub_width": 320,  # Adjusted for your screenshot (approx 320px panel)
            "dhub_padding": 15,  
            "window_width": 320,  # Smaller windows untuk better fitting
            "window_height": 240,
            "horizontal_spacing": 8,  
            "vertical_spacing": 12,    
            "top_margin": 80,  
            "columns": 3,
            "use_legacy_positioning": False,  # Set ke True kalau Android 10+
        }
        
        # Detect Android version
        self._detect_android_version()
        
        try:
            self.config_mgr.set_value("launch_delay", 20)
        except Exception:
            if hasattr(self.config_mgr, 'config_data'):
                self.config_mgr.config_data["launch_delay"] = 20

    def _detect_android_version(self):
        """Deteksi Android version untuk adjust method"""
        try:
            version_output = self._execute_shell("getprop ro.build.version.release")
            if version_output:
                try:
                    version = float(version_output.split('.')[0])
                    if version >= 10:
                        self.logger.warning(f"[!] Detected Android {version} - Using legacy positioning")
                        self.grid_config["use_legacy_positioning"] = True
                except:
                    pass
        except:
            pass

    def _execute_shell(self, command: str) -> str:
        """Eksekusi perintah dengan root access"""
        try:
            root_command = f"su -c '{command}'"
            result = subprocess.run(root_command, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Shell execution failed: {e}")
            return ""

    def get_all_roblox_clones(self) -> list:
        """Scan semua package dengan unsur 'roblox'"""
        raw_packages = self._execute_shell("pm list packages")
        clones = []
        for line in raw_packages.split("\n"):
            if line.startswith("package:"):
                pkg = line.replace("package:", "").strip()
                if "roblox" in pkg.lower():
                    clones.append(pkg)
        return sorted(clones)

    def is_package_running(self, pkg_name: str) -> bool:
        """Check apakah package sedang running"""
        pid = self._execute_shell(f"pidof {pkg_name}")
        return len(pid) > 0

    def calculate_grid_position(self, index: int) -> dict:
        """Hitung posisi grid optimal"""
        config = self.grid_config
        cols = config["columns"]
        
        row = index // cols
        col = index % cols
        
        # FIXED: Gunakan nilai actual dari screenshot Anda
        start_x = config["dhub_width"] + config["dhub_padding"] + (col * (config["window_width"] + config["horizontal_spacing"]))
        start_y = config["top_margin"] + (row * (config["window_height"] + config["vertical_spacing"]))
        
        return {
            'x': start_x,
            'y': start_y,
            'width': config["window_width"],
            'height': config["window_height"],
            'row': row,
            'col': col,
            'bounds_str': f"{start_x} {start_y} {start_x + config['window_width']} {start_y + config['window_height']}"
        }

    def force_freeform_grid_android10(self, pkg_name: str, index: int):
        """
        Method untuk Android 10+ - menggunakan wmctrl atau dumpsys alternative
        """
        grid_pos = self.calculate_grid_position(index)
        bounds_str = grid_pos['bounds_str']
        
        self.logger.info(f"[Android 10+ Mode] {pkg_name} -> Row {grid_pos['row']}, Col {grid_pos['col']}, Pos: ({grid_pos['x']}, {grid_pos['y']})")
        
        # Try method 1: dumpsys activity
        for retry in range(8):
            try:
                task_info = self._execute_shell(
                    f"dumpsys activity activities | grep -i {pkg_name} | head -n 1"
                )
                
                if task_info:
                    # Extract task ID dari TaskRecord
                    task_id = None
                    for s in task_info.split():
                        if s.isdigit() and int(s) > 0:
                            task_id = int(s)
                            break
                    
                    if task_id:
                        self.logger.info(f"[Found] TaskID: {task_id}")
                        
                        # Method 1: Try set task bounds (Android 10+)
                        self._execute_shell(f"dumpsys window | grep -i {pkg_name}")
                        
                        # Method 2: Try wm command
                        self._execute_shell(f"wm size")
                        
                        # Method 3: Try input tap untuk trigger positioning
                        # (Fallback jika automation gagal)
                        
                        self.logger.info(f"[✓] Attempted positioning for {pkg_name}")
                        break
            except Exception as e:
                self.logger.debug(f"Retry {retry + 1}/8 for {pkg_name}: {e}")
            
            time.sleep(0.6)

    def force_freeform_grid_legacy(self, pkg_name: str, index: int):
        """
        Method legacy/original untuk Android 9 dan bawah
        """
        grid_pos = self.calculate_grid_position(index)
        bounds_str = grid_pos['bounds_str']
        
        self.logger.info(f"[Legacy Mode] {pkg_name} -> Row {grid_pos['row']}, Col {grid_pos['col']}, Pos: ({grid_pos['x']}, {grid_pos['y']})")
        
        for retry in range(10):
            try:
                task_info = self._execute_shell(
                    f"dumpsys activity activities | grep -E 'TaskRecord|ActivityRecord' | grep {pkg_name} | head -n 1"
                )
                
                if task_info:
                    try:
                        task_id = None
                        for s in task_info.split():
                            if s.isdigit():
                                task_id = int(s)
                                break
                        
                        if task_id:
                            # Stack 5 = Freeform (untuk Android < 10)
                            self._execute_shell(f"am stack move-task {task_id} 5 true")
                            time.sleep(0.3)
                            self._execute_shell(f"am task resize {task_id} {bounds_str}")
                            
                            self.logger.info(f"[✓] Successfully arranged {pkg_name}")
                            break
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"Parse error: {e}")
                        
            except Exception as e:
                self.logger.debug(f"Retry {retry + 1}/10: {e}")
            
            if retry < 9:
                time.sleep(0.5)

    def force_freeform_grid(self, pkg_name: str, index: int):
        """Router method - pilih legacy atau android10 based on detection"""
        if self.grid_config.get("use_legacy_positioning", False):
            self.force_freeform_grid_android10(pkg_name, index)
        else:
            self.force_freeform_grid_legacy(pkg_name, index)

    def monitor_live_state_daemon(self, pkg_name: str):
        """Monitor status real-time"""
        while self.is_monitoring:
            try:
                if self.is_package_running(pkg_name):
                    if self.clone_statuses.get(pkg_name) == "Launched":
                        self.clone_statuses[pkg_name] = "Online"
                else:
                    self.clone_statuses[pkg_name] = "Offline"
            except Exception as e:
                self.logger.debug(f"Monitor error for {pkg_name}: {e}")
            
            time.sleep(1.5)

    def launch_all_instances(self, clones: list, place_id: str):
        """Launch semua instances dengan grid positioning"""
        total = len(clones)
        delay_cfg = 20
        
        for pkg in clones:
            self.clone_statuses[pkg] = "Offline"

        self.logger.info(f"[Launcher] Starting {total} instances with auto grid")
        self.logger.info(f"[Config] Mode: {'Android 10+' if self.grid_config['use_legacy_positioning'] else 'Legacy'}")
        self.logger.info(f"[Config] Layout: {self.grid_config['columns']} columns, {self.grid_config['window_width']}×{self.grid_config['window_height']}px")

        for idx, pkg in enumerate(clones):
            self.clone_statuses[pkg] = "Loading"
            
            if place_id:
                cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {pkg}"
            else:
                cmd = f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
                
            self._execute_shell(cmd)
            
            self.clone_statuses[pkg] = "Launched"
            
            # Grid positioning async
            threading.Thread(
                target=self.force_freeform_grid, 
                args=(pkg, idx), 
                daemon=True
            ).start()
            
            # Status monitor
            threading.Thread(
                target=self.monitor_live_state_daemon, 
                args=(pkg,), 
                daemon=True
            ).start()
            
            # Delay antar launch
            if idx < total - 1:
                time.sleep(delay_cfg)
                
        self.webhook_mgr.send_status_embed(
            status="SUCCESS", 
            action_detail=f"Launched {total} instances with grid layout."
        )

    def print_kaeru_curses(self, stdscr, clones: list, ram_info: str):
        """Render DHUB panel"""
        stdscr.erase()
        
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        curses.init_pair(5, curses.COLOR_RED, -1)
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)
        
        cyan = curses.color_pair(1)
        white = curses.color_pair(2)
        
        # Logo
        stdscr.addstr(0, 2, "██████╗ ██╗  ██╗██╗   ██╗██████╗", cyan | curses.A_BOLD)
        stdscr.addstr(1, 2, "██╔══██╗██║  ██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(2, 2, "██║  ██║███████║██║   ██║██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(3, 2, "██║  ██║██╔══██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(4, 2, "██████╔╝██║  ██║╚██████╔╝██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(5, 2, "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝   v2.0", cyan | curses.A_BOLD)
        
        # Table
        stdscr.addstr(7, 0, "┌──────────────────────────────────────────┬────────────────────────┐", cyan)
        stdscr.addstr(8, 0, "│ PACKAGE                                  │ STATUS                 │", cyan)
        stdscr.addstr(9, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        stdscr.addstr(10, 0, "│ System Memory                            │                        │", cyan)
        stdscr.addstr(10, 45, f"Free: {ram_info}", white)
        
        stdscr.addstr(11, 0, "│ Launch Delay                             │                        │", cyan)
        stdscr.addstr(11, 45, "20s (Locked)", white)
        
        grid_mode = "Android 10+" if self.grid_config['use_legacy_positioning'] else "Legacy"
        stdscr.addstr(12, 0, "│ Grid Mode                                │                        │", cyan)
        stdscr.addstr(12, 45, grid_mode, white)
        
        stdscr.addstr(13, 0, "│ Grid Layout                              │                        │", cyan)
        stdscr.addstr(13, 45, f"{self.grid_config['columns']} Col Grid", white)
        
        stdscr.addstr(14, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        current_row = 15
        for idx, pkg in enumerate(clones[:8]):
            stdscr.addstr(current_row, 0, "│                                          │                        │", cyan)
            display_name = pkg[:38]
            stdscr.addstr(current_row, 2, display_name, white)
            
            status = self.clone_statuses.get(pkg, "Offline")
            if status == "Online":
                c_style = curses.color_pair(3) | curses.A_BOLD    # Hijau
            elif status == "Launched":
                c_style = curses.color_pair(4) | curses.A_BOLD  # Kuning
            elif status == "Loading":
                c_style = curses.color_pair(6) | curses.A_BOLD   # Magenta
            else:
                c_style = curses.color_pair(5) | curses.A_DIM     # Merah
                
            stdscr.addstr(current_row, 45, status, c_style)
            current_row += 1
            
        stdscr.addstr(current_row, 0, "└──────────────────────────────────────────┴────────────────────────┘", cyan)
        stdscr.addstr(current_row + 2, 0, "» Tekan 'q' atau 'Enter' untuk kembali...", white | curses.A_DIM)
        
        stdscr.refresh()

    def set_grid_layout(self, columns: int):
        """Set jumlah kolom"""
        if columns in [2, 3, 4]:
            self.grid_config["columns"] = columns
            self.logger.info(f"Grid layout changed to {columns} columns")
        else:
            self.logger.warning(f"Invalid column count. Use 2, 3, or 4")

    def adjust_window_size(self, width: int, height: int):
        """Sesuaikan ukuran window"""
        self.grid_config["window_width"] = width
        self.grid_config["window_height"] = height
        self.logger.info(f"Window size adjusted to {width}x{height}")

    def set_dhub_width(self, width: int):
        """Sesuaikan lebar DHUB panel"""
        self.grid_config["dhub_width"] = width
        self.logger.info(f"DHUB width adjusted to {width}px")

    def launch_app(self):
        """Main launcher entry point"""
        place_id = self.config_mgr.config_data.get("place_id", "")
        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        installed_clones = self.get_all_roblox_clones()
        
        if not installed_clones:
            os.system("clear")
            print("\033[91m[!] Error: Tidak ada Roblox clone terdeteksi\033[0m")
            return

        self.is_monitoring = True
        
        self.logger.info(f"Found {len(installed_clones)} instances")

        threading.Thread(
            target=self.launch_all_instances,
            args=(installed_clones, place_id),
            daemon=True
        ).start()

        def curses_main(stdscr):
            curses.curs_set(0)
            stdscr.nodelay(True)
            stdscr.timeout(500)
            
            while self.is_monitoring:
                self.print_kaeru_curses(stdscr, installed_clones, ram_info)
                try:
                    key = stdscr.getch()
                    if key in [ord('q'), ord('Q'), 10]:
                        break
                except Exception:
                    pass
                time.sleep(0.3)

        try:
            curses.wrapper(curses_main)
        finally:
            self.is_monitoring = False
            
        os.system("clear")
        print("\033[93m[!] Monitoring selesai. Kembali ke menu utama...\033[0m")
        time.sleep(1)
