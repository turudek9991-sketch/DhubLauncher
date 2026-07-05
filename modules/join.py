"""
DHub-Rejoin - Professional Orchestrator
Description: Central entry point that delegates logic to modular components.
             Manages LauncherEngine to handle multi-worker threads.
"""

import curses
import time
from modules.launcher import LauncherEngine
from modules.process_manager import ProcessManager
from modules.xml_manager import XMLManager
from modules.grid_manager import GridManager
from modules.status import WorkerStatus

class JoinManager:
    def __init__(self, config_mgr, logger):
        self.config_mgr = config_mgr
        self.logger = logger
        
        # Inisialisasi komponen modular (Dependency Injection)
        self.proc = ProcessManager(logger)
        self.xml = XMLManager(self.proc, logger)
        self.grid = GridManager(config_mgr)
        
        # LauncherEngine menangani inisialisasi Worker
        self.launcher = LauncherEngine(
            self.proc, 
            self.xml, 
            self.grid, 
            logger, 
            config_mgr
        )

    def launch_app(self):
        """Entry point utama untuk meluncurkan sistem self-healing."""
        clones = self.proc.list_clones()
        if not clones:
            print("[!] Tidak ada package Roblox terdeteksi.")
            return

        # Start semua worker (non-blocking)
        self.launcher.start_all()

        # UI Loop menggunakan Curses (memantau status dari setiap worker)
        self._run_ui_loop(clones)

    def _run_ui_loop(self, clones):
        """Rendering TUI (Text User Interface) yang memantau status setiap worker."""
        def curses_main(stdscr):
            curses.curs_set(0)
            stdscr.nodelay(True)
            
            # Setup Color Pairs
            curses.start_color()
            curses.init_pair(1, curses.COLOR_CYAN, -1)   # Header & Border
            curses.init_pair(2, curses.COLOR_WHITE, -1)  # Normal Text
            curses.init_pair(3, curses.COLOR_GREEN, -1)  # Online
            curses.init_pair(4, curses.COLOR_YELLOW, -1) # Restarting/Loading
            curses.init_pair(5, curses.COLOR_RED, -1)    # Error

            while True:
                stdscr.erase()
                
                # Header UI - Mempertahankan branding KAERU/DHUB
                stdscr.addstr(0, 2, "██████╗ ██╗  ██╗██╗   ██╗██████╗", curses.color_pair(1) | curses.A_BOLD)
                stdscr.addstr(1, 2, "██╔══██╗██║  ██║██║   ██║██╔══██╗", curses.color_pair(1))
                stdscr.addstr(2, 2, "██║  ██║███████║██║   ██║██████╔╝", curses.color_pair(1))
                stdscr.addstr(3, 2, "██║  ██║██╔══██║██║   ██║██╔══██╗", curses.color_pair(1))
                stdscr.addstr(4, 2, "██████╔╝██║  ██║╚██████╔╝██████╔╝", curses.color_pair(1))
                stdscr.addstr(5, 2, "DHub Pro - Professional Multi-Worker System", curses.color_pair(1) | curses.A_BOLD)
                
                # Header Tabel
                stdscr.addstr(7, 2, "PACKAGE" + " " * 25 + "| STATUS", curses.color_pair(1) | curses.A_UNDERLINE)

                # Render status setiap worker
                for i, pkg in enumerate(clones):
                    worker = self.launcher.workers.get(pkg)
                    status_enum = worker.status if worker else WorkerStatus.OFFLINE
                    
                    # Warna status dinamis berdasarkan Enum
                    color = curses.color_pair(2)
                    if status_enum == WorkerStatus.ONLINE: color = curses.color_pair(3)
                    elif status_enum in [WorkerStatus.RESTARTING, WorkerStatus.LOADING, WorkerStatus.LAUNCHING]: color = curses.color_pair(4)
                    elif status_enum == WorkerStatus.ERROR: color = curses.color_pair(5)
                    
                    stdscr.addstr(i + 8, 2, f"{pkg[:30]:<30} | ", curses.color_pair(2))
                    stdscr.addstr(i + 8, 35, f"{status_enum.value}", color | curses.A_BOLD)
                
                stdscr.addstr(len(clones) + 10, 2, "» Tekan 'q' atau 'Enter' untuk kembali.", curses.color_pair(1) | curses.A_DIM)
                
                stdscr.refresh()
                
                key = stdscr.getch()
                if key in [ord('q'), ord('Q'), 10]:
                    break
                time.sleep(1)

        try:
            curses.wrapper(curses_main)
        finally:
            # Shutdown bersih semua thread worker
            self.launcher.stop_all()
