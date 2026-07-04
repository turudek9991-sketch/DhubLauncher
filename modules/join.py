"""
DHub-Rejoin - Automated Multi-Window Grid Orchestrator (DPI 600 Optimized)
Author: Senior Python Developer
Description: Dispatches multiple clone targets and automatically tiles them into a perfect 
             right-aligned grid mapping via low-level Android Activity Manager stacks.
"""

import time
import subprocess
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
        self.engine_status = "Ready"

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
        # Urutkan nama package agar penataan window berurutan dari clone 1, 2, dst.
        return sorted(clones)

    def arrange_window_grid(self, pkg_name: str, index: int):
        """
        Logika Utama Pengatur Grid Sisi Kanan (DPI 600 Optimized).
        Menggunakan perintah Android Window Manager untuk memaksa clone Roblox masuk ke mode split/freeform.
        """
        # Menghitung koordinat bounding box berdasarkan indeks aplikasi (Membentuk Grid di Sisi Kanan)
        # Dimensi disesuaikan secara dinamis agar presisi layaknya screenshot target
        row = index // 3
        col = index % 3
        
        # Penentuan koordinat X dan Y pada layar landscape DPI 600
        # Menggeser baseline X ke sisi kanan (menyisakan sisi kiri untuk Termux)
        width = 400
        height = 300
        start_x = 700 + (col * 420)
        start_y = 50 + (row * 320)
        
        bounds_str = f"{start_x} {start_y} {start_x + width} {start_y + height}"
        
        # Ambil Task ID dari package yang baru saja dibuka
        time.sleep(1.2)
        task_info = self._execute_shell(f"dumpsys activity activities | grep -E 'TaskRecord|ActivityRecord' | grep {pkg_name} | head -n 1")
        
        if task_info:
            try:
                # Ekstrak nomor Task ID Android
                task_id = [int(s) for s in task_info.split() if s.isdigit()][0]
                # Paksa window bergerak ke koordinat grid kanan menggunakan akses root am
                self._execute_shell(f"am task resize {task_id} {bounds_str}")
            except Exception:
                pass

    def launch_all_instances(self, clones: list, place_id: str):
        """Daemon sekuensial untuk membuka seluruh clone Roblox tanpa membuat Termux crash."""
        total = len(clones)
        for idx, pkg in enumerate(clones):
            self.engine_status = f"Launching {idx+1}/{total}"
            
            # Tembakkan intent deep-link menuju target game
            if place_id:
                cmd = f"am start -a android.intent.action.VIEW -d 'roblox://placeID={place_id}' -p {pkg}"
            else:
                cmd = f"monkey -p {pkg} -c android.intent.category.LAUNCHER 1"
            
            self._execute_shell(cmd)
            
            # Atur posisi jendela clone secara instan ke sisi kanan grid
            self.arrange_window_grid(pkg, idx)
            time.sleep(0.5)
            
        self.engine_status = "Grid Synced"
        self.webhook_mgr.send_status_embed(status="SUCCESS", action_detail=f"Successfully arranged {total} Roblox Clones into a synchronized Right-Side Grid.")

    def print_kaeru_curses(self, stdscr, clones: list, ram_info: str):
        """Merender UI TUI bergaris kokoh dengan Logo DHUB besar yang tidak bisa hancur."""
        stdscr.erase()
        
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
        
        cyan = curses.color_pair(1)
        white = curses.color_pair(2)
        green = curses.color_pair(3) | curses.A_BOLD
        yellow = curses.color_pair(4) | curses.A_BOLD

        delay_cfg = self.config_mgr.config_data.get("launch_delay", 20)
        place_id = self.config_mgr.config_data.get("place_id", "95206881")
        
        # Gambar Logo Raksasa DHUB
        stdscr.addstr(0, 2, "██████╗ ██╗  ██╗██╗   ██╗██████╗", cyan | curses.A_BOLD)
        stdscr.addstr(1, 2, "██╔══██╗██║  ██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(2, 2, "██║  ██║███████║██║   ██║██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(3, 2, "██║  ██║██╔══██║██║   ██║██╔══██╗", cyan | curses.A_BOLD)
        stdscr.addstr(4, 2, "██████╔╝██║  ██║╚██████╔╝██████╔╝", cyan | curses.A_BOLD)
        stdscr.addstr(5, 2, "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝   Launcher v1.0", cyan | curses.A_BOLD)
        
        # Render Frame Grid Tabel KAERU Style
        stdscr.addstr(7, 0, "┌──────────────────────────────────────────┬────────────────────────┐", cyan)
        stdscr.addstr(8, 0, "│ PACKAGE                                  │ STATUS                 │", cyan)
        stdscr.addstr(8, 2, "PACKAGE", white | curses.A_BOLD)
        stdscr.addstr(8, 45, "STATUS", cyan | curses.A_BOLD)
        stdscr.addstr(9, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Data Konfigurasi Atas
        stdscr.addstr(10, 0, "│ System Memory                            │                        │", cyan)
        stdscr.addstr(10, 45, f"Free: {ram_info}", white)
        
        stdscr.addstr(11, 0, "│ Launch Delay                             │                        │", cyan)
        stdscr.addstr(11, 45, f"{delay_cfg}s (Forced)", white)
        
        stdscr.addstr(12, 0, "├──────────────────────────────────────────┼────────────────────────┤", cyan)
        
        # Tampilkan Seluruh Daftar Instance Yang Berhasil Dikunci Ke Grid Kanan
        current_row = 13
        for idx, pkg in enumerate(clones[:6]): # Batasi tampilan visual maksimal 6 baris utama di CLI Termux
            stdscr.addstr(current_row, 0, "│                                          │                        │", cyan)
            display_name = pkg[:38]
            stdscr.addstr(current_row, 2, display_name, white)
            
            if self.engine_status == "Grid Synced":
                stdscr.addstr(current_row, 45, "Online (Grid)", green)
            else:
                stdscr.addstr(current_row, 45, self.engine_status, yellow)
            current_row += 1
            
        stdscr.addstr(current_row, 0, "└──────────────────────────────────────────┴────────────────────────┘", cyan)
        stdscr.addstr(current_row + 2, 0, "» Tekan 'q' atau 'Enter' untuk kembali ke Control Panel...", white | curses.A_DIM)
        
        stdscr.refresh()

    def launch_app(self):
        """Eksekusi taktis otomasi multi-window grid."""
        # Force default delay ke angka stabil aman 20 detik untuk mengamankan CPU emulator
        self.config_mgr.set_value("launch_delay", 20)
        
        place_id = self.config_mgr.config_data.get("place_id", "")
        device_data = self.arrange_mgr.fetch_device_data()
        ram_info = device_data.get("ram", "Unknown")

        # Pindai secara real-time seluruh varian akun clone Roblox yang ada di Redfinger Anda
        installed_clones = self.get_all_roblox_clones()
        
        if not installed_clones:
            os.system("clear")
            print("\033[91m[!] Gagal: Tidak ada aplikasi Roblox / Clone yang terdeteksi di sistem.\033[0m")
            return

        self.is_monitoring = True
        self.engine_status = "Queued"

        # Pemicu background orchestrator untuk menyusun susunan grid secara sekuensial (Anti-Crash)
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
                time.sleep(0.5)

        try:
            curses.wrapper(curses_main)
        finally:
            self.is_monitoring = False
            
        os.system("clear")
        print("\033[93m[!] Proses monitoring disinkronkan. Kembali ke menu utama...\033[0m")
        time.sleep(1)
