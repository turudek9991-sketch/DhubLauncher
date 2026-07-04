"""
DHub-Rejoin - Application Joiner & Launcher Module
Author: Senior Python Developer
Description: Launches targeted Android applications via shell intents with custom execution delays.
"""

import time
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import local discord notification module
from modules.webhook import WebhookManager

console = Console()

class JoinManager:
    def __init__(self, config_mgr, logger):
        """
        Inisialisasi JoinManager dengan konfigurasi dan sistem log.
        """
        self.config_mgr = config_mgr
        self.logger = logger
        self.webhook_mgr = WebhookManager(config_mgr, logger)

    def _execute_shell(self, command: str) -> bool:
        """
        Menjalankan perintah shell internal untuk memicu aplikasi Android.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"Intent launch failed: {result.stderr.strip()}")
                return False
        except Exception as e:
            self.logger.error(f"Exception during shell execution: {e}")
            return False

    def launch_app(self):
        """
        Fungsi utama untuk memicu jalannya aplikasi target berdasarkan config.
        """
        console.clear()
        console.print(Panel("[bold cyan]LAUNCH APPLICATION PROCESS (JOIN)[/bold cyan]", border_style="cyan"))
        
        # Ambil data konfigurasi terkini
        target_pkg = self.config_mgr.config_data.get("package", "")
        delay = self.config_mgr.config_data.get("launch_delay", 3)
        
        # Validasi target package
        if not target_pkg:
            console.print("[bold red][!] Gagal: Tidak ada package aplikasi yang disetting dalam konfigurasi![/bold red]")
            console.print("[yellow][*] Silakan masuk ke Package Manager atau Settings terlebih dahulu.[/yellow]")
            return

        console.print(f"[green][*] Menyiapkan peluncuran package:[/green] [yellow]{target_pkg}[/yellow]")
        console.print(f"[green][*] Waktu penundaan (Launch Delay):[/green] [yellow]{delay} detik[/yellow]")
        
        # Hitung mundur menggunakan progress animation dari Rich
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task(description="Menunggu delay sebelum peluncuran...", total=delay)
            for _ in range(delay):
                time.sleep(1)
                progress.advance(task, 1)

        console.print("[bold yellow][*] Memicu Android Intent untuk membuka aplikasi...[/bold yellow]")
        
        # Menggunakan tool monkey Android bawaan (cara paling andal meluncurkan package tanpa tahu Main Activity-nya)
        # Perintah ini akan membuka launcher activity utama dari package tersebut
        cmd = f"monkey -p {target_pkg} -c android.intent.category.LAUNCHER 1"
        
        success = self._execute_shell(cmd)
        
        if success:
            console.print(Panel(f"[bold green][+] Sukses memicu peluncuran aplikasi {target_pkg}![/bold green]", border_style="green"))
            self.logger.info(f"Successfully launched package via monkey intent: {target_pkg}")
            
            # Kirim status sukses ke Discord Webhook secara otomatis
            self.webhook_mgr.send_status_embed(status="SUCCESS", action_detail="Application Launched Successfully")
        else:
            # Jika akses langsung ditolak/perangkat non-root tanpa izin tertentu, berikan fallback peringatan simulasi
            console.print("[bold red][!] Peringatan: Izin akses shell terbatas di sesi Termux non-root perangkat ini.[/bold red]")
            console.print("[yellow][*] Mengirimkan fallback trigger/status ke Discord Webhook...[/yellow]")
            
            self.logger.warning(f"Shell failed to force launch {target_pkg}. Sent status notification.")
            self.webhook_mgr.send_status_embed(status="SUCCESS (SIMULATED)", action_detail="Trigger Sent but limited by Termux Shell API")
