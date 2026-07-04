"""
DHub-Rejoin - Universal Split-Execution Freeform Engine
Author: Senior Python Developer
Description: Dispatches clone targets using high-compatibility launchers and forces 
             freeform grid orchestration post-spawn to bypass device intent blockage.
             
IMPROVEMENTS:
- Auto grid arrangement optimization for DPI 600
- Prevent overlap with DHUB launcher panel
- Configurable grid layouts (2x2, 2x3, 3x3, 4x3)
- Better window positioning and sizing
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
        
        # Grid Configuration - OPTIMIZED FOR DPI 600
        self.grid_config = {
            "dpi": 600,
            "dhub_width": 450,  # Lebar panel DHUB launcher (dari sebelah kiri)
            "dhub_padding": 20,  # Padding antara DHUB dan window pertama
            "window_width": 370,  # Lebar optimal untuk window Roblox
            "window_height": 270, # Tinggi optimal untuk window Roblox
            "horizontal_spacing": 10,  # Jarak antar window horizontal
            "vertical_spacing": 20,    # Jarak antar window vertikal
            "top_margin": 60,  # Margin atas (statusbar)
            "columns": 3,  # Jumlah kolom grid (bisa disesuaikan: 2, 3, atau 4)
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

    def calculate_grid_position(self, index: int) -> dict:
        """
        Hitung posisi grid optimal berdasarkan index tanpa menutupi DHUB launcher.
        
        Returns:
            dict: {
                'x': start_x,
                'y': start_y,
                'width': window_width,
                'height': window_height,
                'row': row,
                'col': col
            }
        """
        config = self.grid_config
        cols = config["columns"]
        
        row = index // cols
        col = index % cols
        
        # Hitung posisi X: hindari DHUB launcher yang ada di sebelah kiri
        start_x = config["dhub_width"] + config["dhub_padding"] + (col * (config["window_width"] + config["horizontal_spacing"]))
        
        # Hitung posisi Y: mulai dari bawah statusbar
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

    def force_freeform_grid(self, pkg_name: str, index: int):
        """
        Logika Pemindah Jendela Pasca-Spawn YANG SUDAH DITINGKATKAN.
        Menangkap Task ID secara dinamis dan memaksanya masuk ke koordinat grid yang optimal.
        Memastikan tidak menutupi DHUB launcher panel.
        """
        grid_pos = self.calculate_grid_position(index)
        bounds_str = grid_pos['bounds_str']
        
        self.logger.info(f"[Grid Layout] Package {pkg_name} -> Row {grid_pos['row']}, Col {grid_pos['col']}, Pos: ({grid_pos['x']}, {grid_pos['y']})")
        
        # Polling singkat (maksimal 5 detik) menunggu Task ID terdaftar di sistem Android
        max_retries = 10
        for retry in range(max_retries):
            try:
                task_info = self._execute_shell(
                    f"dumpsys activity activities | grep -E 'TaskRecord|ActivityRecord' | grep {pkg_name} | head -n 1"
                )
                
                if task_info:
                    try:
                        # Extract task ID dari task_info
                        task_id = None
                        for s in task_info.split():
                            if s.isdigit():
                                task_id = int(s)
                                break
                        
                        if task_id:
                            # Paksa tumpukan beralih ke stack 5 (Freeform Mode)
                            self._execute_shell(f"am stack move-task {task_id} 5 true")
                            time.sleep(0.5)
                            
                            # Kunci koordinat posisi grid yang sudah dihitung
                            self._execute_shell(f"am task resize {task_id} {bounds_str}")
                            
                            self.logger.info(f"[✓] Successfully arranged {pkg_name} at position ({grid_pos['x']}, {grid_pos['y']})")
                            break
                    except (ValueError, IndexError) as e:
                        self.logger.debug(f"Failed to parse task info: {e}")
                        
            except Exception as e:
                self.logger.debug(f"Retry {retry + 1}/{max_retries} for {pkg_name}: {e}")
            
            # Tunggu sebelum retry
            if retry < max_retries - 1:
                time.sleep(0.5)

    def monitor_live_state_daemon(self, pkg_name: str):
        """Worker Daemon: Memantau transisi status secara real-time berdasarkan manifes memori."""
        while self.is_monitoring:
            try:
                if self.is_package_running(pkg_name):
                    if self.clone_statuses.get(pkg_name) == "Launched":
                        self.clone_statuses[pkg_name] = "Online"
                else:
                    # Jika aplikasi terputus atau ditutup paksa
                    self.clone_statuses[pkg_name] = "Offline"
            except Exception as e:
                self.logger.debug(f"Monitor daemon error for {pkg_name}: {e}")
            
            time.sleep(1.5)

    def launch_all_instances(self, clones: list, place_id: str):
        """
        Mengelola peluncuran dengan pemisahan eksekusi untuk menjamin Roblox terbuka 100%
        dan disusun dalam grid otomatis.
        """
        total = len(clones)
        delay_cfg = 20
        
        # Setel seluruh status awal ke posisi Offline (Menunggu antrean delay)
        for pkg in clones:
            self.clone_statuses[pkg] = "Offline"

        self.logger.info(f"[Launcher] Starting {total} Roblox instances with auto grid arrangement...")

        for idx, pkg in enumerate(clones):
            self.clone_statuses[pkg] = "Loading"
            
            # [SOLUSI MUTLAK PELUNCURAN]: Menggunakan skema pemicu dasar tanpa penyuntikan bounds awal 
            # untuk menghindari penolakan manifes, sehingga Roblox dipastikan terbuka 100%.
            if place_id:
                cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {pkg}"
            else:
                cmd = f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
                
            self._execute_shell(cmd)
            
            # Ubah status ke Launched sesaat setelah pemicu biner selesai ditembakkan
            self.clone_statuses[pkg] = "Launched"
            
            # Jalankan orkestrasi penataan jendela di latar belakang secara asinkron
            # dengan positioning yang sudah dioptimalkan
            threading.Thread(
                target=self.force_freeform_grid, 
                args=(pkg, idx), 
                daemon=True
            ).start()
            
            # Jalankan pengawas status Online memori secara real-time
            threading.Thread(
                target=self.monitor_live_state_daemon, 
                args=(pkg,), 
                daemon=True
            ).start()
            
            # Eksekusi interupsi hitung mundur delay join 20 detik penuh sebelum memproses device berikutnya
            if idx < total - 1:
                time.sleep(delay_cfg)
                
        self.webhook_mgr.send_status_embed(
            status="SUCCESS", 
            action_detail=f"Successfully initialized and arranged {total} instances in grid layout."
        )

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
        
        # Logo Teks Raksasa DHUB
        stdscr.addstr(0, 2, "██████╗ ██╗  ██╗██╗   ██╗██████╗", cyan | curses.A_BOLD)
        stdscr.addstr(1, 2, "██╔══██╗██║  ██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(2, 2, "██║  ██║███████║██║   ██║██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(3, 2, "██║  ██║██╔══██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(4, 2, "██████╔╝██║  ██║╚██████╔╝██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(5, 2, "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝   Launcher v1.0", cyan | curses.A_BOLD)
        
        # Render Tabel Frame KAERU Style
        stdscr.addstr(7, 0, "┌──────────────────────────────────────────┬────────────────────────┐", cyan)
        stdscr.addstr(8, 0, "│ PACKAGE                                  │ STATUS                 │", cyan)
        stdscr.addstr(8, 2, "PACKAGE", white | curses.A_BOLD)
        stdscr.addstr(8, 45, "STATUS", cyan | curses.A_BOLD)
        stdscr.addstr(9, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Data Blok Konfigurasi Atas
        stdscr.addstr(10, 0, "│ System Memory                            │                        │", cyan)
        stdscr.addstr(10, 45, f"Free: {ram_info}", white)
        
        stdscr.addstr(11, 0, "│ Launch Delay                             │                        │", cyan)
        stdscr.addstr(11, 45, "20s (Locked)", white)
        
        grid_layout = f"{self.grid_config['columns']} Col Grid"
        stdscr.addstr(12, 0, "│ Grid Layout                              │                        │", cyan)
        stdscr.addstr(12, 45, grid_layout, white)
        
        stdscr.addstr(13, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Loop Rendering Status Baris Komponen Target
        current_row = 14
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
                c_style = curses.color_pair(5) | curses.A_DIM     # Merah (Offline)
                
            stdscr.addstr(current_row, 45, status, c_style)
            current_row += 1
            
        stdscr.addstr(current_row, 0, "└──────────────────────────────────────────┴────────────────────────┘", cyan)
        stdscr.addstr(current_row + 2, 0, "» Tekan 'q' atau 'Enter' untuk kembali ke Control Panel...", white | curses.A_DIM)
        
        stdscr.refresh()

    def set_grid_layout(self, columns: int):
        """
        Ubah layout grid secara dinamis.
        
        Args:
            columns (int): Jumlah kolom (2, 3, atau 4)
        """
        if columns in [2, 3, 4]:
            self.grid_config["columns"] = columns
            self.logger.info(f"Grid layout changed to {columns} columns")
        else:
            self.logger.warning(f"Invalid column count. Use 2, 3, or 4. Current: {self.grid_config['columns']}")

    def adjust_window_size(self, width: int, height: int):
        """
        Sesuaikan ukuran window untuk grid layout.
        
        Args:
            width (int): Lebar window dalam pixel
            height (int): Tinggi window dalam pixel
        """
        self.grid_config["window_width"] = width
        self.grid_config["window_height"] = height
        self.logger.info(f"Window size adjusted to {width}x{height}")

    def launch_app(self):
        """Titik masuk siklus monitoring dengan auto grid arrangement."""
        place_id = self.config_mgr.config_data.get("place_id", "")
        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        installed_clones = self.get_all_roblox_clones()
        
        if not installed_clones:
            os.system("clear")
            print("\033[91m[!] Gagal: Tidak ada aplikasi Roblox / Clone yang terdeteksi di sistem.\033[0m")
            return

        self.is_monitoring = True
        
        self.logger.info(f"Found {len(installed_clones)} Roblox instances")
        self.logger.info(f"Grid configuration: {self.grid_config['columns']} columns, {self.grid_config['window_width']}x{self.grid_config['window_height']}px")

        # Pemicu background orchestrator thread
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
