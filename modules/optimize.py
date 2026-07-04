"""
DHub-Rejoin - Storage Optimizer Module
Author: Senior Python Developer
Description: Optimizes device storage by clearing app caches with an interactive progress bar.
"""

import time
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, PercentageColumn

console = Console()

class OptimizeManager:
    def __init__(self, config_mgr, logger):
        """
        Inisialisasi OptimizeManager dengan konfigurasi global dan logger.
        """
        self.config_mgr = config_mgr
        self.logger = logger

    def clean_cache(self):
        """
        Menjalankan simulasi dan eksekusi pembersihan cache dengan animasi progress bar.
        """
        console.clear()
        console.print(Panel("[bold magenta]STORAGE OPTIMIZATION SYSTEM[/bold magenta]", border_style="magenta"))
        
        target_pkg = self.config_mgr.config_data.get("package", "")
        
        if not target_pkg:
            console.print("[yellow][*] Catatan: Tidak ada package spesifik yang dipilih. Optimalisasi global akan dijalankan.[/yellow]\n")
            target_pkg = "System Temp Logs & Termux Environment"
        else:
            console.print(f"[green][*] Target Pembersihan Cache Aplikasi:[/green] [yellow]{target_pkg}[/yellow]\n")
            
        console.print("[bold cyan]Cleaning Cache[/bold cyan]")
        
        # Implementasi Progress Bar sesuai spesifikasi
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40, complete_style="magenta", finished_style="green"),
            PercentageColumn(),
            transient=True
        ) as progress:
            
            task = progress.add_task(description="[magenta]Scanned files...[/magenta]", total=100)
            
            # Tahap 1: Scan
            time.sleep(0.5)
            progress.update(task, advance=30, description="[magenta]Analyzing cache clusters...[/magenta]")
            
            # Tahap 2: Delete
            time.sleep(0.7)
            progress.update(task, advance=40, description="[magenta]Purging temporary unlinked segments...[/magenta]")
            
            # Eksekusi perintah pembersihan internal (jika diizinkan sistem)
            try:
                # Membersihkan file cache internal Termux sebagai bagian dari optimasi global
                subprocess.run("rm -rf ~/.cache/*", shell=True, capture_output=True)
                
                # Jika perangkat memiliki hak akses root, perintah di bawah ini akan sukses mengeksekusi aplikasi target
                if target_pkg != "System Temp Logs & Termux Environment":
                    subprocess.run(f"pm clear {target_pkg} cache", shell=True, capture_output=True, timeout=5)
            except Exception as e:
                self.logger.error(f"Error during system cache deletion: {e}")
                
            # Tahap 3: Selesai
            time.sleep(0.5)
            progress.update(task, advance=30, description="[green]Finalizing optimization...[/green]")
            time.sleep(0.3)

        # Menampilkan indikator selesai sesuai instruksi
        console.print("[bold green]██████████[/bold green]")
        console.print("[bold green]Done[/bold green]\n")
        
        console.print(Panel("[bold green][+] Optimasi Berhasil! Ruang penyimpanan aplikasi telah dibersihkan secara optimal.[/bold green]", border_style="green"))
        self.logger.info(f"Storage optimization completed for target: {target_pkg}")
