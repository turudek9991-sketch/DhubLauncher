"""
DHub-Rejoin - Configuration Management Module
Author: Senior Python Developer
Description: Handles JSON-based persistent configuration profiles.
"""

import os
import json

class ConfigManager:
    def __init__(self, logger, config_path: str = "config.json"):
        """
        Inisialisasi ConfigManager dengan jalur file target dan objek logger.
        """
        self.config_path = config_path
        self.logger = logger
        # Template default jika file config.json kosong atau hilang
        self.config_data = {
            "package": "",
            "launch_delay": 3,
            "theme": "dark",
            "discord_webhook": "",
            "autosave": True,
            "log_level": "INFO"
        }

    def load_config(self) -> dict:
        """
        Memuat konfigurasi dari file json. Jika file tidak ada, file baru akan dibuat.
        """
        if not os.path.exists(self.config_path):
            self.logger.info(f"{self.config_path} not found. Creating a new defaults template.")
            self.save_config()
            return self.config_data
            
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                # Lakukan sinkronisasi data agar key baru tidak terlewat
                for key, val in loaded_data.items():
                    self.config_data[key] = val
            self.logger.info("Configuration loaded successfully from disk.")
        except Exception as e:
            self.logger.error(f"Error loading JSON configuration file: {e}")
            
        return self.config_data

    def save_config(self) -> bool:
        """
        Menulis state konfigurasi internal saat ini kembali ke file disk json.
        """
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to write configuration to file: {e}")
            return False

    def set_value(self, key: str, value):
        """
        Mengubah parameter konfigurasi dan menyimpannya secara otomatis jika fitur autosave aktif.
        """
        self.config_data[key] = value
        
        # Sesuai aturan spesifikasi parameter autosave
        if self.config_data.get("autosave", True):
            self.save_config()
            self.logger.info(f"Configuration key '{key}' autosaved onto disk.")
