"""
DHub-Rejoin - App Cloner XML Grid Engine (Super Compact Frame Fix)
Author: Senior Python Developer
Description: Bypasses Android WindowManager limitations by directly modifying App Cloner's
             shared_preferences XML layout properties using micro right-side bounds.
"""

import time
import os
import curses
import threading

from modules.grid_manager import GridManager
from modules.launcher import LauncherEngine
from modules.process_manager import ProcessManager
from modules.status import PackageStatus
from modules.xml_manager import XMLManager

class JoinManager:
    def __init__(self, config_mgr, logger):
        self.config_mgr = config_mgr
        self.logger = logger
        
        from modules.webhook import WebhookManager
        from modules.arrange import ArrangeManager
        
        self.webhook_mgr = WebhookManager(config_mgr, logger)
        self.arrange_mgr = ArrangeManager(config_mgr, logger)
        self.proc = ProcessManager(logger)
        
        self.is_monitoring = False
        self.clone_statuses = {}
        
        # [SUPER COMPACT KAERU MATRIX - DPI 600 HARD LOCK]
        # Ukuran dan margin disusutkan maksimal agar fit sempurna di frame Redfinger
        self.grid_config = {
            "start_x_base": 660,        # Geser merapat ke Termux agar sisi kanan tidak luber keluar frame
            "window_width": 180,        # SUPER MINI: Lebar proporsional window melayang
            "window_height": 100,       # SUPER MINI: Tinggi proporsional window melayang
            "columns": 2,               # Formasi tetap 2 kolom ke samping di wilayah kanan
            "top_margin": 60,           # Batas aman dari status bar atas
            "gap": 5                    # Celah minimalis antar jendela
        }
        self.grid_mgr = GridManager(self.grid_config)
        self.xml_mgr = XMLManager(self.proc)
        self.launcher_engine = LauncherEngine(
            config_mgr,
            logger,
            process_manager=self.proc,
            grid_manager=self.grid_mgr,
            xml_manager=self.xml_mgr
        )
        
        try:
            self.config_mgr.set_value("launch_delay", 5)
        except Exception:
            if hasattr(self.config_mgr, 'config_data'):
                self.config_mgr.config_data["launch_delay"] = 5

    def get_all_roblox_clones(self) -> list:
        return self.launcher_engine.scan_packages()

    def is_package_running(self, pkg_name: str) -> bool:
        return self.proc.is_running(pkg_name)

    def calculate_xml_coordinates(self, index: int) -> dict:
        return self.grid_mgr.calculate_xml_coordinates(index)

    def inject_coordinates_to_xml(self, pkg_name: str, coords: dict) -> bool:
        return self.xml_mgr.inject(pkg_name, coords)

    def launch_all_instances(self, clones: list, place_id: str):
        self.launcher_engine.start(place_id=place_id, packages=clones)

    def print_kaeru_curses(self, stdscr, clones: list, ram_info: str):
        """Merender TUI Panel legendaris KAERU yang kokoh, rapi, dan simetris di layar Termux."""
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
        stdscr.addstr(5, 2, "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝   Launcher v1.0 - @dimsgti", cyan | curses.A_BOLD)
        
        # Bingkai Tabel Estetis KAERU
        stdscr.addstr(7, 0, "┌──────────────────────────────────────────┬────────────────────────┐", cyan)
        stdscr.addstr(8, 0, "│ PACKAGE                                  │ STATUS                 │", cyan)
        stdscr.addstr(8, 2, "PACKAGE", white | curses.A_BOLD)
        stdscr.addstr(8, 45, "STATUS", cyan | curses.A_BOLD)
        stdscr.addstr(9, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Informasi Konfigurasi Engine
        stdscr.addstr(10, 0, "│ System Memory                            │                        │", cyan)
        stdscr.addstr(10, 45, f"Free: {ram_info}", white)
        
        stdscr.addstr(11, 0, "│ Launch Delay                             │                        │", cyan)
        stdscr.addstr(11, 45, "5s (Locked)", white)
        
        stdscr.addstr(12, 0, "│ Duration                                 │                        │", cyan)
        stdscr.addstr(12, 45, "Lifetime", white)
        
        stdscr.addstr(13, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        current_row = 14
        for idx, pkg in enumerate(clones[:8]):
            stdscr.addstr(current_row, 0, "│                                          │                        │", cyan)
            display_name = pkg[:38]
            stdscr.addstr(current_row, 2, display_name, white)
            
            status = self.clone_statuses.get(pkg, PackageStatus.Offline)
            status_text = status.value if isinstance(status, PackageStatus) else str(status)
            if status_text == PackageStatus.Online.value:
                c_style = curses.color_pair(3) | curses.A_BOLD
            elif status_text == PackageStatus.Launching.value:
                c_style = curses.color_pair(4) | curses.A_BOLD
            elif status_text == PackageStatus.Loading.value:
                c_style = curses.color_pair(6) | curses.A_BOLD
            else:
                c_style = curses.color_pair(5) | curses.A_DIM
                
            stdscr.addstr(current_row, 45, status_text, c_style)
            current_row += 1
            
        stdscr.addstr(current_row, 0, "└──────────────────────────────────────────┴────────────────────────┘", cyan)
        stdscr.addstr(current_row + 2, 0, "» Tekan 'q' atau 'Enter' untuk kembali ke Control Panel...", white | curses.A_DIM)
        
        stdscr.refresh()

    def launch_app(self):
        place_id = self.config_mgr.config_data.get("place_id", "")
        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        installed_clones = self.launcher_engine.scan_packages()
        
        if not installed_clones:
            os.system("clear")
            print("\033[91m[!] Gagal: Tidak ada aplikasi Roblox Clone terdeteksi.\033[0m")
            return

        self.is_monitoring = True
        self.clone_statuses = self.launcher_engine.get_statuses()

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
            self.launcher_engine.stop()
            
        os.system("clear")
        print("\033[93m[!] Proses monitoring disinkronkan. Kembali ke menu utama...\033[0m")
        time.sleep(1)
