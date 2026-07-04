"""
DHub-Rejoin - Application Joiner & Launcher Module (Root Optimized)
Author: Senior Python Developer
Description: Launches targeted Android applications via root shell intents for cloud emulators.
"""

import time
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

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
        Menjalankan perintah shell internal dengan hak akses superuser (root).
        """
        try:
            # Memaksa perintah berjalan menggunakan hak akses root
            root_command = f"su -c '{command}'"
            result = subprocess.run(
                root_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"Root intent launch failed: {result.stderr.strip()}")
                return False
        except Exception as e:
            self.logger.error(f"Exception during root shell execution: {e}")
            return False

    def launch_app(self):
        """
        Fungsi utama untuk memicu peluncuran aplikasi clone target menggunakan akses superuser.
        """
        console.clear()
        console.print(Panel("[bold cyan]LAUNCH APPLICATION PROCESS (JOIN)[/bold cyan]", border_style="cyan"))
        
        target_pkg = self.config_mgr.config_data.get("package", "")
        delay = self.config_mgr.config_data.get("launch_delay", 3)
        
        if not target_pkg:
            console.print("[bold red][!] Gagal: Tidak ada package aplikasi yang dikunci dalam konfigurasi![/bold red]")
            return

        console.print(f"[green][*] Menyiapkan peluncuran package:[/green] [yellow]{target_pkg}[/yellow]")
        console.print(f"[green][*] Waktu penundaan (Launch Delay):[/green] [yellow]{delay} detik[/yellow]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task(description="Menunggu delay sebelum peluncuran...", total=delay)
            for _ in range(delay):
                time.sleep(1)
                progress.advance(task, 1)

        console.print("[bold yellow][*] Memicu Superuser Android Intent untuk membuka clone...[/bold yellow]")
        
        # Perintah monkey dijalankan melalui akses root superuser
        cmd = f"monkey -p {target_pkg} -c android.intent.category.LAUNCHER 1"
        
        success = self._execute_shell(cmd)
        
        if success:
            console.print(Panel(f"[bold green][+] Sukses memicu peluncuran aplikasi {target_pkg} via Root! [/bold green]", border_style="green"))
            self.logger.info(f"Successfully launched package via root monkey intent: {target_pkg}")
            self.webhook_mgr.send_status_embed(status="SUCCESS", action_detail=f"Application {target_pkg} Launched via Root Context")
        else:
            console.print("[bold red][!] Peringatan: Eksekusi Root Intent gagal merespon.[/bold red]")
            console.print("[yellow][*] Mengirimkan status laporan ke Discord Webhook...[/yellow]")
            self.webhook_mgr.send_status_embed(status="FAILED", action_detail=f"Failed to force launch {target_pkg} via Root Context")
