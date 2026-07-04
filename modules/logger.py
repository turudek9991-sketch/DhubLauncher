"""
DHub-Rejoin - Logger Module
Author: Senior Python Developer
Description: Custom stream and file logger matching precise layout requirements.
"""

import os
import datetime

class AppLogger:
    def __init__(self):
        """
        Inisialisasi manajer log. Memastikan direktori logs siap dipakai.
        """
        self.log_dir = "logs"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _write_log(self, message: str):
        """
        Fungsi internal untuk menulis pesan log ke file dengan format waktu bersih.
        """
        now = datetime.datetime.now()
        # Nama file mengikuti tanggal hari ini: YYYY-MM-DD.log
        date_str = now.strftime("%Y-%m-%d")
        file_path = os.path.join(self.log_dir, f"{date_str}.log")
        
        # Format isi log: [HH:MM:SS]\nMessage\n
        time_str = now.strftime("%H:%M:%S")
        log_entry = f"[{time_str}]\n{message}\n"
        
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            # Silent fallback untuk mencegah CLI crash akibat kendala I/O file internal
            pass

    def info(self, message: str):
        """
        Mencatat pesan log dengan tingkat prioritas INFO.
        """
        self._write_log(message)

    def warning(self, message: str):
        """
        Mencatat pesan log dengan tingkat prioritas WARNING.
        """
        self._write_log(f"WARNING: {message}")

    def error(self, message: str):
        """
        Mencatat pesan log dengan tingkat prioritas ERROR.
        """
        self._write_log(f"ERROR: {message}")
