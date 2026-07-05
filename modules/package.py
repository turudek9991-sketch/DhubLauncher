"""
DHub-Rejoin - Package Manager Module (Instant Auto-Save)
Author: Senior Python Developer
Description: Scans Android app packages for Roblox/Clones and instantly saves the target to config without user prompt.
"""

import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from modules.process_manager import ProcessManager

console = Console()

class PackageManager:
    def __init__(self, config_mgr, logger):
        """
        Inisialisasi PackageManager dengan manajemen konfigurasi dan logger.
        """
        self.config_mgr = config_mgr
        self.logger = logger
        self.proc = ProcessManager(logger)

    def _execute_shell(self, command: str) -> str:
        """
        Helper internal untuk mengeksekusi perintah shell Android dengan aman.
        """
        return self.proc.run_plain(command)

    def get_package_version(self, package_name: str) -> str:
        """
        Mendapatkan versi dari package tertentu menggunakan perintah dumpsys.
        """
        return self.proc.get_package_version(package_name)

    def scan_installed_packages(self) -> list:
        """
        Memindai package Android yang mengandung kata kunci 'roblox' (Mendukung Multi-Instance/Clone).
        """
        console.print("[yellow][*] Memindai database aplikasi di perangkat... Mohon tunggu...[/yellow]")
        
        raw_output = "\n".join(f"package:{pkg}" for pkg in self.proc.list_package_names(keyword="roblox"))
        
        # Jalur simulasi fallback jika di lingkungan non-Android atau kosong
        if not raw_output:
            return [
                {"name": "com.roblox.seiyv", "version": "Unknown", "status": "Clone Detected"}
            ]

        lines = raw_output.split("\n")
        packages_list = []
        
        for line in lines:
            if line.startswith("package:"):
                pkg_name = line.replace("package:", "").strip()
                
                # Filter deteksi clone Roblox
                if pkg_name and "roblox" in pkg_name.lower():
                    version = self.get_package_version(pkg_name)
                    
                    if pkg_name == "com.roblox.client":
                        status_label = "Original App"
                    else:
                        status_label = "Clone Detected"
                        
                    packages_list.append({
                        "name": pkg_name,
                        "version": version,
                        "status": status_label
                    })
                    
        return packages_list

    def manage_packages(self):
        """
        Fungsi utama menu Package Manager - Otomatis mendeteksi dan langsung menyimpan ke config.
        """
        console.clear()
        console.print(Panel("[bold green]AUTOMATIC ROBLOX DETECTOR & AUTO-SAVE[/bold green]", border_style="green"))
        
        packages = self.scan_installed_packages()
        
        if not packages:
            console.print("[bold red][!] Tidak ada package berunsur 'roblox' terdeteksi di perangkat ini.[/bold red]")
            return

        # Konstruksi tabel visual untuk konfirmasi kepada pengguna aplikasi apa saja yang diamankan
        table = Table(title="Daftar Target Terdeteksi & Disimpan", header_style="bold magenta")
        table.add_column("No", justify="center", style="cyan")
        table.add_column("Nama Package Aplikasi", justify="left", style="white")
        table.add_column("Versi", justify="center", style="green")
        table.add_column("Klasifikasi", justify="center", style="yellow")
        
        for idx, pkg in enumerate(packages, start=1):
            table.add_row(str(idx), pkg["name"], pkg["version"], pkg["status"])
            
        console.print(table)
        console.print(f"\n[bold]Total Terdeteksi:[/bold] {len(packages)} Package Varian Roblox")
        
        # [PROSES AUTO SAVE INSTAN]
        # Mengambil package pertama yang ditemukan (sangat cocok untuk single clone terfokus di instance tersebut)
        selected_pkg = packages[0]["name"]
        
        # Jika clone lebih dari satu dan Anda ingin menyimpan semuanya sekaligus dipisahkan koma, 
        # Anda bisa menggunakan baris ini: selected_pkg = ",".join([p["name"] for p in packages])
        
        # Tulis langsung data ke config global tanpa bertanya
        self.config_mgr.set_value("package", selected_pkg)
        self.logger.info(f"Auto-saved package target onto config: {selected_pkg}")
        
        console.print(Panel(
            f"[bold green][+] SUKSES AUTO-SAVE![/bold green]\n"
            f"Target [yellow]{selected_pkg}[/yellow] telah berhasil dikunci secara otomatis ke pengaturan Anda.", 
            border_style="green"
        ))
