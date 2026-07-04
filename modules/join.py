"""
DHub-Rejoin - Android 10+ Advanced Task Organizer Engine
Author: Senior Python Developer
Description: Uses the modern 'cmd window' API to strictly contain and grid floating 
             Roblox instances on the right half of landscape DPI 600 screens.
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
        
        # Grid Configuration - OPTIMIZED FOR DPI 600 (Landscape Mode Right-Side Grid)
        self.grid_config = {
            "dhub_width": 730,          # Menyisakan ruang sebelah kiri bersih untuk Termux
            "window_width": 380,        # Lebar window aplikasi melayang
            "window_height": 260,       # Tinggi window aplikasi melayang
            "columns": 3,               # Maksimal 3 kolom ke samping di sisi kanan
            "top_margin": 70,           # Margin atas agar tidak tertutup status bar
            "horizontal_spacing": 12,   
            "vertical_spacing": 12,
        }
        
        try:
            self.config_mgr.set_value("launch_delay", 20)
        except Exception:
            if hasattr(self.config_mgr, 'config_data'):
                self.config_mgr.config_data["launch_delay"] = 20

    def _execute_shell(self, command: str) -> str:
        """Eksekusi perintah internal dengan hak akses superuser root."""
        try:
            root_command = f"su -c '{command}'"
            result = subprocess.run(root_command, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout.strip()
        except Exception as e:
            self.logger.error(f"Root Execution failed: {e}")
            return ""

    def get_all_roblox_clones(self) -> list:
        """Memindai sistem secara instan untuk mencari semua package yang terinstal dengan unsur 'roblox'."""
        raw_packages = self._execute_shell("pm list packages")
        clones = []
        for line in raw_packages.split("\n"):
            if line.startswith("package:"):
                pkg = line.replace("package:", "").strip()
                if "roblox" in pkg.lower():
                    clones.append(pkg)
        return sorted(clones)

    def is_package_running(self, pkg_name: str) -> bool:
        """Memeriksa apakah proses Android package aktif menggunakan perintah pidof."""
        pid = self._execute_shell(f"pidof {pkg_name}")
        return len(pid) > 0

    def calculate_grid_bounds(self, index: int) -> str:
        """Menghitung koordinat piksel landscape secara presisi di wilayah kanan layar."""
        cfg = self.grid_config
        row = index // cfg["columns"]
        col = index % cfg["columns"]
        
        start_x = cfg["dhub_width"] + (col * (cfg["window_width"] + cfg["horizontal_spacing"]))
        start_y = cfg["top_margin"] + (row * (cfg["window_height"] + cfg["vertical_spacing"]))
        
        # Format Android 10+: left top right bottom
        return f"{start_x} {start_y} {start_x + cfg['window_width']} {start_y + cfg['window_height']}"

    def force_freeform_grid(self, pkg_name: str, index: int):
        """
        Logika Utama Pengatur Grid Sisi Kanan (Android 10+ Modern API).
        Menggunakan perintah 'cmd window' untuk memaksa mode freeform dan resize koordinat secara instan.
        """
        bounds_str = self.calculate_grid_bounds(index)
        
        # Polling tunggu maksimal 6 detik sampai jendela Roblox terdaftar di ActivityManager
        for _ in range(12):
            if not self.is_monitoring:
                break
                
            task_info = self._execute_shell(f"dumpsys activity activities | grep -E 'TaskRecord|ActivityRecord' | grep {pkg_name} | head -n 1")
            if task_info:
                try:
                    task_id = [int(s) for s in task_info.split() if s.isdigit()][0]
                    
                    # [METODE MODEREN ANDROID 10+]:
                    # 1. Gunakan 'cmd window' untuk set mode freeform secara kaku ke task ID aplikasi
                    self._execute_shell(f"cmd window set-freeform {task_id}")
                    time.sleep(0.3)
                    
                    # 2. Paksa Android Window Manager memotong dimensi sesuai bounds grid kanan
                    self._execute_shell(f"cmd window set-bounds {task_id} {bounds_str}")
                    
                    # Fallback jika 'cmd window' tidak merespon di beberapa custom ROM Redfinger
                    self._execute_shell(f"am stack move-task {task_id} 5 true")
                    self._execute_shell(f"am task resize {task_id} {bounds_str}")
                    break
                except Exception:
                    pass
            time.sleep(0.5)

    def monitor_live_state_daemon(self, pkg_name: str):
        """Worker Daemon: Memantau transisi status memori secara real-time (Online/Offline)."""
        while self.is_monitoring:
            if self.is_package_running(pkg_name):
                if self.clone_statuses.get(pkg_name) == "Launched":
                    self.clone_statuses[pkg_name] = "Online"
            else:
                self.clone_statuses[pkg_name] = "Offline"
            time.sleep(1.5)

    def launch_all_instances(self, clones: list, place_id: str):
        """Mengelola siklus peluncuran bertahap dengan penundaan 20 detik anti-crash."""
        total = len(clones)
        delay_cfg = 20
        
        for pkg in clones:
            self.clone_statuses[pkg] = "Offline"

        for idx, pkg in enumerate(clones):
            self.clone_statuses[pkg] = "Loading"
            
            if place_id:
                cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {pkg}"
            else:
                cmd = f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
                
            self._execute_shell(cmd)
            self.clone_statuses[pkg] = "Launched"
            
            # Jalankan penataan Freeform Grid via Modern API secara asinkron
            threading.Thread(target=self.force_freeform_grid, args=(pkg, idx), daemon=True).start()
            
            # Jalankan monitor status Online
            threading.Thread(target=self.monitor_live_state_daemon, args=(pkg,), daemon=True).start()
            
            # Terapkan jeda 20 detik penuh antar-device agar emulator tidak overload/freeze
            if idx < total - 1:
                time.sleep(delay_cfg)
                
        self.webhook_mgr.send_status_embed(status="SUCCESS", action_detail=f"Successfully deployed {total} instances into right-side grid.")

    def print_kaeru_curses(self, stdscr, clones: list, ram_info: str):
        """Merender TUI Panel legendaris KAERU yang kokoh, rapi, dan simetris di layar."""
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
        
        # Logo Teks Besar DHUB
        stdscr.addstr(0, 2, "██████╗ ██╗  ██╗██╗   ██╗██████╗", cyan | curses.A_BOLD)
        stdscr.addstr(1, 2, "██╔══██╗██║  ██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(2, 2, "██║  ██║███████║██║   ██║██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(3, 2, "██║  ██║██╔══██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(4, 2, "██████╔╝██║  ██║╚██████╔╝██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(5, 2, "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝   Launcher v2.0", cyan | curses.A_BOLD)
        
        # Bingkai Tabel
        stdscr.addstr(7, 0, "┌──────────────────────────────────────────┬────────────────────────┐", cyan)
        stdscr.addstr(8, 0, "│ PACKAGE                                  │ STATUS                 │", cyan)
        stdscr.addstr(8, 2, "PACKAGE", white | curses.A_BOLD)
        stdscr.addstr(8, 45, "STATUS", cyan | curses.A_BOLD)
        stdscr.addstr(9, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Info Atas
        stdscr.addstr(10, 0, "│ System Memory                            │                        │", cyan)
        stdscr.addstr(10, 45, f"Free: {ram_info}", white)
        
        stdscr.addstr(11, 0, "│ Launch Delay                             │                        │", cyan)
        stdscr.addstr(11, 45, "20s (Locked)", white)
        
        stdscr.addstr(12, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Cetak baris package kloningan secara berurutan
        current_row = 13
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
        stdscr.addstr(current_row + 2, 0, "» Tekan 'q' atau 'Enter' untuk kembali ke Control Panel...", white | curses.A_DIM)
        
        stdscr.refresh()

    def launch_app(self):
        """Titik masuk utama eksekusi."""
        place_id = self.config_mgr.config_data.get("place_id", "")
        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        installed_clones = self.get_all_roblox_clones()
        
        if not installed_clones:
            os.system("clear")
            print("\033[91m[!] Gagal: Tidak ada aplikasi Roblox / Clone yang terdeteksi di sistem.\033[0m")
            return

        self.is_monitoring = True

        # Jalankan background orchestrator
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
        print("\033[93m[!] Proses monitoring disinkronkan. Kembali ke menu utama...\033[0m")
        time.sleep(1)
