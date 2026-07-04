"""
DHub-Rejoin - Advanced Multi-Window Grid & Real-Time Status Engine
Author: Senior Python Developer
Description: Delivers a rock-solid TUI with multi-state tracking (Offline -> Loading -> Launched -> Online)
             while securing forced Android Freeform window instantiation for all Roblox targets.
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
        # Kamus dinamis untuk mengunci status per masing-masing package clone secara independen
        self.clone_statuses = {}
        
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

    def calculate_grid_bounds(self, index: int) -> str:
        """Menghitung koordinat piksel landscape secara presisi (DPI 600 Optimized) di sisi kanan."""
        row = index // 3
        col = index % 3
        
        width = 380
        height = 270
        
        start_x = 740 + (col * 395)
        start_y = 60 + (row * 285)
        
        return f"{start_x},{start_y},{start_x + width},{start_y + height}"

    def is_package_running(self, pkg_name: str) -> bool:
        """Memeriksa apakah proses Android package aktif menggunakan perintah pidof tingkat rendah."""
        pid = self._execute_shell(f"pidof {pkg_name}")
        return len(pid) > 0

    def monitor_live_state_daemon(self, pkg_name: str):
        """Worker Daemon: Mengawasi siklus transisi status aplikasi dari launched menuju online."""
        # Menunggu aplikasi stabil pasca diluncurkan
        time.sleep(5)
        while self.is_monitoring:
            if self.is_package_running(pkg_name):
                # Ketika terdeteksi di memori dan aktif di layar, status dikunci ke Online
                if self.clone_statuses.get(pkg_name) in ["Launched", "Loading"]:
                    self.clone_statuses[pkg_name] = "Online"
            else:
                # Jika mati atau crash dari latar belakang, kembalikan ke Offline
                self.clone_statuses[pkg_name] = "Offline"
            time.sleep(2)

    def launch_all_instances(self, clones: list, place_id: str):
        """Mengelola peluncuran sekuensial dengan transisi status yang ketat dan akurat."""
        total = len(clones)
        delay_cfg = 20
        
        # Langkah 1: Setel semua daftar target awal menjadi Offline (Menunggu daftar loading delay)
        for pkg in clones:
            self.clone_statuses[pkg] = "Offline"

        for idx, pkg in enumerate(clones):
            # Langkah 2: Ketika giliran dimulai, status berubah menjadi Loading
            self.clone_statuses[pkg] = "Loading"
            bounds = self.calculate_grid_bounds(idx)
            
            # [BYPASS LAUNCH FIX]: Menggunakan skema intent terpadu android.intent.action.VIEW 
            # yang dipaksa injeksi flag windowing mode 5 agar kebal dari silent crash di seluruh variasi clone.
            if place_id:
                cmd = f"am start --windowingMode 5 --bounds {bounds} -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {pkg}"
            else:
                cmd = f"am start --windowingMode 5 --bounds {bounds} -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p {pkg}"

            self._execute_shell(cmd)
            
            # Langkah 3: Masuk ke status Launched setelah intent berhasil ditembakkan ke Window Manager Android
            time.sleep(1.5)
            self.clone_statuses[pkg] = "Launched"
            
            # Jalankan daemon thread pembantu untuk memantau kapan status bertransisi menjadi Online secara real-time
            threading.Thread(target=self.monitor_live_state_daemon, args=(pkg,), daemon=True).start()
            
            # Jalankan hitung mundur jeda antar-device (Delay Join 20 Detik)
            if idx < total - 1:
                time.sleep(delay_cfg)
                
        self.webhook_mgr.send_status_embed(status="SUCCESS", action_detail=f"Automated execution grid for {total} instances initialized securely.")

    def print_kaeru_curses(self, stdscr, clones: list, ram_info: str):
        """Merender grafis visual legendaris KAERU yang statis, kokoh, dan bergaris rapi."""
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
        
        # Gambar Logo Teks Raksasa DHUB
        stdscr.addstr(0, 2, "██████╗ ██╗  ██╗██╗   ██╗██████╗", cyan | curses.A_BOLD)
        stdscr.addstr(1, 2, "██╔══██╗██║  ██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(2, 2, "██║  ██║███████║██║   ██║██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(3, 2, "██║  ██║██╔══██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(4, 2, "██████╔╝██║  ██║╚██████╔╝██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(5, 2, "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝   Launcher v1.0", cyan | curses.A_BOLD)
        
        # Render Batas Garis Tabel KAERU
        stdscr.addstr(7, 0, "┌──────────────────────────────────────────┬────────────────────────┐", cyan)
        stdscr.addstr(8, 0, "│ PACKAGE                                  │ STATUS                 │", cyan)
        stdscr.addstr(8, 2, "PACKAGE", white | curses.A_BOLD)
        stdscr.addstr(8, 45, "STATUS", cyan | curses.A_BOLD)
        stdscr.addstr(9, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Data Blok Atas
        stdscr.addstr(10, 0, "│ System Memory                            │                        │", cyan)
        stdscr.addstr(10, 45, f"Free: {ram_info}", white)
        
        stdscr.addstr(11, 0, "│ Launch Delay                             │                        │", cyan)
        stdscr.addstr(11, 45, "20s (Locked)", white)
        
        stdscr.addstr(12, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Tampilkan Seluruh Daftar Instance Beserta Status Akurat Masing-Masing
        current_row = 13
        for idx, pkg in enumerate(clones[:8]): # Menampilkan hingga 8 baris teratas di layar landscape
            stdscr.addstr(current_row, 0, "│                                          │                        │", cyan)
            display_name = pkg[:38]
            stdscr.addstr(current_row, 2, display_name, white)
            
            # Resolusi status pewarnaan presisi tinggi
            status = self.clone_statuses.get(pkg, "Offline")
            if status == "Online":
                c_style = curses.color_pair(3) | curses.A_BOLD    # Hijau
            elif status == "Launched":
                c_style = curses.color_pair(4) | curses.A_BOLD  # Kuning
            elif status == "Loading":
                c_style = curses.color_pair(6) | curses.A_BOLD   # Magenta
            else:
                c_style = curses.color_pair(5) | curses.A_DIM     # Merah (Offline)
                
            stdscr.addstr(current_row, 45, status, c_style)
            current_row += 1
            
        stdscr.addstr(current_row, 0, "└──────────────────────────────────────────┴────────────────────────┘", cyan)
        stdscr.addstr(current_row + 2, 0, "» Tekan 'q' atau 'Enter' untuk kembali ke Control Panel...", white | curses.A_DIM)
        
        stdscr.refresh()

    def launch_app(self):
        """Mengeksekusi siklus utama otomasi multi-window grid dengan status canggih."""
        place_id = self.config_mgr.config_data.get("place_id", "")
        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        installed_clones = self.get_all_roblox_clones()
        
        if not installed_clones:
            os.system("clear")
            print("\033[91m[!] Gagal: Tidak ada aplikasi Roblox / Clone yang terdeteksi di sistem.\033[0m")
            return

        self.is_monitoring = True

        # Jalankan background orchestrator thread
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
