"""
DHub-Rejoin - Discord Webhook Integration Module (Fix Post Payload)
Author: Senior Python Developer
Description: Dispatches structured diagnostic and status reports using Discord Embeds.
"""

import datetime
import requests
from rich.console import Console

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
        Membentuk format objek Discord Embed dan mengirimkannya ke URL Webhook.
        """
        url = self.config_mgr.config_data.get("discord_webhook", "")
        
        if not url or not url.startswith("http"):
            self.logger.warning("Discord Webhook URL is empty or invalid in config.json.")
            console.print("[yellow][!] Peringatan: URL Discord Webhook belum diatur dengan benar di menu Settings.[/yellow]")
            return False

        device_info = self.arrange_mgr.fetch_device_data()
        target_app = self.config_mgr.config_data.get("package", "None Selected")
        embed_color = 3066993 if "SUCCESS" in status else 15158332
        
        payload = {
            "username": "DHub-Rejoin Bot",
            "embeds": [
                {
                    "title": "DHub-Rejoin Operational Report",
                    "description": "Aktivitas pemicu peluncuran aplikasi pada lingkungan Termux.",
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
                        {"name": "Execution Time", "value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": False}
                    ],
                    "footer": {
                        "text": "DHub Open-Source Engine Core"
                    }
                }
            ]
        }

        try:
            # Perbaikan: Mengirim data JSON secara eksplisit menggunakan argumen json=payload
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            if response.status_code in [200, 204]:
                console.print("[bold green][+] Berhasil mengirim status embed ke Discord Webhook![/bold green]")
                self.logger.info(f"Discord report pushed successfully. Status: {status}")
                return True
            else:
                self.logger.error(f"Discord Webhook API rejected payload. Status Code: {response.status_code}")
                console.print(f"[bold red][!] Gagal: Server Discord merespon dengan kode {response.status_code}[/bold red]")
                return False
        except Exception as e:
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
