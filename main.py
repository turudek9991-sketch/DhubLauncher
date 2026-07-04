#!/usr/bin/env python3
"""
DHub Launcher - Main Entry Point (Fixed Loop)
Author: Senior Python Developer
Version: 1.0.0
Description: Main script to initialize and run the Termux-based Android launcher without auto-trigger bugs.
"""

import os
import sys
from modules.logger import AppLogger
from modules.config import ConfigManager
from modules.menu import MainMenu
from modules.banner import show_banner

def initialize_project():
    """
    Memastikan semua direktori yang dibutuhkan tersedia dan menginisialisasi modul utama.
    """
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    logger = AppLogger()
    logger.info("Application Started")
    
    config_mgr = ConfigManager(logger)
    config_mgr.load_config()
    
    return config_mgr, logger

def main():
    """
    Fungsi utama yang mengendalikan alur eksekusi aplikasi dan loop menu.
    """
    try:
        # Inisialisasi modul
        config_mgr, logger = initialize_project()
        
        # Instance MainMenu untuk mengelola navigasi
        menu = MainMenu(config_mgr, logger)
        
        # LOOP UTAMA: Hanya jalankan apa yang dipilih oleh user!
        while True:
            # Tampilkan Banner Utama
            show_banner(config_mgr)
            
            # Tampilkan Menu Interaktif dan Dapatkan Pilihan User
            choice = menu.display_main_menu()
            
            # Eksekusi Pilihan secara ketat
            if not menu.execute_choice(choice):
                logger.info("Application Stopped by User")
                break
                
    except KeyboardInterrupt:
        print("\n\n[!] Gagal: Aplikasi dihentikan paksa (Ctrl+C).")
        sys.exit(0)
    except Exception as e:
        print(f"\n[!] Terjadi kesalahan fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
