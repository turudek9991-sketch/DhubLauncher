"""
DHub-Rejoin - App Cloner XML Grid Engine (Kaeru Method Replica)
Author: Senior Python Developer
Description: Bypasses Android WindowManager limitations by directly modifying App Cloner's
             shared_preferences XML layout properties before issuing launch state intents.
"""

import time
import subprocess
import os
import curses
import threading
import xml.etree.ElementTree as ET

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
        
        # [KAERU MATRIX - DPI 600 OPTIMIZED]
        # Koordinat dihitung kaku agar membagi sisi kanan secara simetris layaknya Kaeru Tools
        self.grid_config = {
            "start_x_base": 720,        # Menjauh dari area kiri (Termux aman dari tumpukan)
            "window_width": 420,        # Lebar proporsional jendela Roblox melayang
            "window_height": 280,       # Tinggi proporsional jendela Roblox melayang
            "columns": 2,               # Formasi 2 kolom ke samping di wilayah kanan
            "top_margin": 60,           # Batas aman dari status bar atas
            "gap": 6
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

    def calculate_xml_coordinates(self, index: int) -> dict:
        """Menghitung koordinat Rectangle (Left, Top, Right, Bottom) berdasarkan konfigurasi grid Kaeru."""
        cfg = self.grid_config
        row = index // cfg["columns"]
        col = index % cfg["columns"]
        
        left = cfg["start_x_base"] + (col * (cfg["window_width"] + cfg["gap"]))
        top = cfg["top_margin"] + (row * (cfg["window_height"] + cfg["gap"]))
        right = left + cfg["window_width"]
        bottom = top + cfg["window_height"]
        
        return {"left": left, "top": top, "right": right, "bottom": bottom}

    def inject_coordinates_to_xml(self, pkg_name: str, coords: dict) -> bool:
        """
        [THE TRUE LAUNCHER REVOLUTION]:
        Menyalin file preference XML ke direktori lokal Termux, memodifikasi tag koordinat 
        App Cloner secara presisi, lalu mengembalikannya ke folder data root dengan hak akses penuh.
        """
        remote_xml_path = f"/data/user/0/{pkg_name}/shared_prefs/{pkg_name}_preferences.xml"
        local_temp_path = f"/tmp/{pkg_name}_prefs.xml"
        
        # 1. Pastikan folder /tmp lokal Termux tersedia
        os.makedirs("/tmp", exist_ok=True)
        
        # 2. Tarik file XML preferences milik aplikasi clone target dari folder root ke lokal Termux
        self._execute_shell(f"cp {remote_xml_path} {local_temp_path}")
        self._execute_shell(f"chmod 777 {local_temp_path}")
        
        if not os.path.exists(local_temp_path) or os.path.getsize(local_temp_path) == 0:
            return False # Fallback jika file preferensi belum terinisialisasi oleh App Cloner
            
        try:
            tree = ET.parse(local_temp_path)
            root = tree.getroot()
            
            # Map target key XML preferensi penataan posisi milik App Cloner
            target_keys = {
                "app_cloner_current_window_left": str(coords["left"]),
                "app_cloner_current_window_top": str(coords["top"]),
                "app_cloner_current_window_right": str(coords["right"]),
                "app_cloner_current_window_bottom": str(coords["bottom"])
            }
            
            # Perbarui nilai int yang sudah ada atau buat baru jika belum terdaftar
            elements_updated = 0
            for key, value in target_keys.items():
                found = False
                for elem in root.findall("int"):
                    if elem.get("name") == key:
                        elem.set("value", value)
                        found = True
                        elements_updated += 1
                        break
                if not found:
                    new_elem = ET.SubElement(root, "int", name=key, value=value)
                    elements_updated += 1
                    
            # Simpan modifikasi XML secara lokal di Termux
            tree.write(local_temp_path, encoding="utf-8", xml_declaration=True)
            
            # 3. Kembalikan file XML yang sudah dimodifikasi ke direktori root data Android
            self._execute_shell(f"cp {local_temp_path} {remote_xml_path}")
            # Setel kepemilikan owner & permission kaku (chown) agar Android mau membacanya saat startup
            self._execute_shell(f"chmod 660 {remote_xml_path}")
            
            # Hapus file sampah lokal Termux
            if os.path.exists(local_temp_path):
                os.remove(local_temp_path)
                
            return True
        except Exception:
            return False

    def monitor_live_state_daemon(self, pkg_name: str):
        """Worker Daemon: Memantau status memori secara real-time (Online/Offline)."""
        time.sleep(5)
        while self.is_monitoring:
            if self.is_package_running(pkg_name):
                if self.clone_statuses.get(pkg_name) in ["Launched", "Loading"]:
                    self.clone_statuses[pkg_name] = "Online"
            else:
                self.clone_statuses[pkg_name] = "Offline"
            time.sleep(2.0)

    def launch_all_instances(self, clones: list, place_id: str):
        """Siklus utama orkestrasi mutakhir berbasis modifikasi XML injector."""
        total = len(clones)
        delay_cfg = 20
        
        for pkg in clones:
            self.clone_statuses[pkg] = "Offline"

        for idx, pkg in enumerate(clones):
            self.clone_statuses[pkg] = "Loading"
            
            # 1. Pastikan aplikasi target dimatikan paksa (Force Stop) agar state memori bersih 
            # dan App Cloner wajib membaca ulang file XML saat inisialisasi awal
            self._execute_shell(f"am force-stop {pkg}")
            time.sleep(0.5)
            
            # 2. Hitung posisi grid Kaeru dan suntikkan langsung ke dalam file preferences.xml
            coords = self.calculate_xml_coordinates(idx)
            self.inject_coordinates_to_xml(pkg, coords)
            
            # 3. Tembakkan intent untuk meluncurkan Roblox clone
            if place_id:
                cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {pkg} --activity-brought-to-front"
            else:
                main_act = self._execute_shell(f"cmd package resolve-activity --brief {pkg} | tail -n 1")
                if main_act and "/" in main_act:
                    cmd = f"am start -n {main_act} --activity-brought-to-front"
                else:
                    cmd = f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
                
            self._execute_shell(cmd)
            self.clone_statuses[pkg] = "Launched"
            
            # Jalankan monitor status Online
            threading.Thread(target=self.monitor_live_state_daemon, args=(pkg,), daemon=True).start()
            
            # Jeda 20 detik penuh antar device peluncuran agar aman bebas dari crash memori
            if idx < total - 1:
                time.sleep(delay_cfg)

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
        stdscr.addstr(5, 2, "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝   Launcher v4.0", cyan | curses.A_BOLD)
        
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
        stdscr.addstr(11, 45, "20s (Locked)", white)
        
        stdscr.addstr(12, 0, "│ Engine Mode                              │                        │", cyan)
        stdscr.addstr(12, 45, "AppCloner XML Grid Injection", white)
        
        stdscr.addstr(13, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        current_row = 14
        for idx, pkg in enumerate(clones[:8]):
            stdscr.addstr(current_row, 0, "│                                          │                        │", cyan)
            display_name = pkg[:38]
            stdscr.addstr(current_row, 2, display_name, white)
            
            status = self.clone_statuses.get(pkg, "Offline")
            if status == "Online":
                c_style = curses.color_pair(3) | curses.A_BOLD
            elif status == "Launched":
                c_style = curses.color_pair(4) | curses.A_BOLD
            elif status == "Loading":
                c_style = curses.color_pair(6) | curses.A_BOLD
            else:
                c_style = curses.color_pair(5) | curses.A_DIM
                
            stdscr.addstr(current_row, 45, status, c_style)
            current_row += 1
            
        stdscr.addstr(current_row, 0, "└──────────────────────────────────────────┴────────────────────────┘", cyan)
        stdscr.addstr(current_row + 2, 0, "» Tekan 'q' atau 'Enter' untuk kembali ke Control Panel...", white | curses.A_DIM)
        
        stdscr.refresh()

    def launch_app(self):
        place_id = self.config_mgr.config_data.get("place_id", "")
        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        installed_clones = self.get_all_roblox_clones()
        
        if not installed_clones:
            os.system("clear")
            print("\033[91m[!] Gagal: Tidak ada aplikasi Roblox Clone terdeteksi di perangkat.\033[0m")
            return

        self.is_monitoring = True

        # Luncurkan background orchestrator thread
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
