"""
DHub-Rejoin - Discord Webhook Integration Module
Author: Senior Python Developer
Description: Dispatches structured diagnostic and status reports using Discord Embeds.
"""

import datetime
import requests
from rich.console import Console

# Import ArrangeManager untuk menyuplai spesifikasi perangkat secara real-time
from modules.arrange import ArrangeManager

console = Console()

class WebhookManager:
    def __init__(self, config_mgr, logger):
        """
        Inisialisasi WebhookManager dengan konfigurasi global dan logger.
        """
        self.config_mgr = config_mgr
        self.logger = logger
        self.arrange_mgr = ArrangeManager(config_mgr, logger)

    def send_status_embed(self, status: str = "SUCCESS", action_detail: str = "Manual Webhook Test Triggered") -> bool:
        """
        Membentuk format objek Discord Embed dan mengirimkannya ke URL Webhook yang disimpan di config.
        """
        url = self.config_mgr.config_data.get("discord_webhook", "")
        
        if not url:
            self.logger.warning("Discord Webhook URL is empty in config.json. Skipping transmission.")
            console.print("[yellow][!] Peringatan: URL Discord Webhook belum diatur di menu Settings.[/yellow]")
            return False

        # Ambil data spesifikasi perangkat saat ini untuk dilampirkan ke Embed
        device_info = self.arrange_mgr.fetch_device_data()
        target_app = self.config_mgr.config_data.get("package", "None Selected")
        
        # Penentuan warna border embed (Hijau untuk Success, Merah untuk Failed)
        embed_color = 3066993 if "SUCCESS" in status else 15158332 # Decimal color codes
        
        # Konstruksi Payload JSON sesuai struktur Discord Webhook API
        payload = {
            "username": "DHub-Rejoin Bot",
            "avatar_url": "https://i.imgur.com/4M34hi2.png",
            "embeds": [
                {
                    "title": "DHub-Rejoin Operational Report",
                    "description": f"Aktivitas pemicu peluncuran aplikasi pada lingkungan Termux.",
                    "color": embed_color,
                    "fields": [
                        {"name": "Application Target", "value": f"`{target_app}`", "inline": True},
                        {"name": "Launcher Version", "value": "v1.0.0", "inline": True},
                        {"name": "Status Execution", "value": f"**{status}**", "inline": True},
                        {"name": "Action Detail", "value": action_detail, "inline": False},
                        {"name": "Android OS Version", "value": device_info["android_version"], "inline": True},
                        {"name": "Device Hardware", "value": f"{device_info['brand']} {device_info['device']}", "inline": True},
                        {"name": "RAM Capacity", "value": device_info["ram"], "inline": True},
                        {"name": "CPU Architecture", "value": device_info["cpu"], "inline": True},
                        {"name": "Execution Time (WIB)", "value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": False}
                    ],
                    "footer": {
                        "text": "DHub Open-Source Engine Core",
                        "icon_url": "https://i.imgur.com/4M34hi2.png"
                    }
                }
            ]
        }

        try:
            response = requests.post(payload=None, json=payload, headers={"Content-Type": "application/json"}, url=url, timeout=10)
            if response.status_code in [200, 204]:
                console.print("[bold green][+] Berhasil mengirim status embed ke Discord Webhook![/bold green]")
                self.logger.info(f"Discord report pushed successfully. Status: {status}")
                return True
            else:
                self.logger.error(f"Discord Webhook API rejected payload. Status Code: {response.status_code}")
                console.print(f"[bold red][!] Gagal: Server Discord merespon dengan kode {response.status_code}[/bold red]")
                return False
        except Exception as e:
            # Jika koneksi gagal total atau error transmisi lainnya, catat status FAILED
            self.logger.error(f"Status FAILED - Discord Webhook connection exception: {e}")
            console.print("[bold red][!] Status: FAILED. Tidak dapat terhubung ke server Discord API.[/bold red]")
            return False

    def test_webhook(self):
        """
        Fungsi pemicu manual untuk menguji konektivitas webhook langsung dari menu utama.
        """
        console.clear()
        console.print("[bold cyan][*] Menguji pengiriman sinyal Discord Webhook...[/bold cyan]")
        self.send_status_embed(status="SUCCESS (TEST POLLING)", action_detail="User initiated diagnostic test directly from CLI Menu.")
