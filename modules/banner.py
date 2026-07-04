"""
DHub-Rejoin - Banner Core Module
Author: Senior Python Developer
Description: Renders the primary application logo branding and system package summary counters.
"""

from rich.console import Console
from rich.panel import Panel

console = Console()

def show_banner(config_mgr):
    """
    Menampilkan banner utama DHub-Rejoin beserta status ringkasan package aktif.
    """
    console.clear()
    
    # Text-art banner minimalis dan modern
    banner_text = (
        "[bold cyan]██████╗  ██╗  ██╗██╗   ██╗██████╗ \n"
        "██╔══██╗ ██║  ██║██║   ██║██╔══██╗\n"
        "██║  ██║ ███████║██║   ██║██████╔╝\n"
        "██║  ██║ ██╔══██║██║   ██║██╔══██╗\n"
        "██████╔╝ ██║  ██║╚██████╔╝██████╔╝\n"
        "╚═════╝  ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ [/bold cyan]\n"
        "=====================================\n"
        "         [bold green]DHub Launcher Core[/bold green]          \n"
        "            Version 1.0.0            \n"
        "====================================="
    )
    
    console.print(banner_text)
    
    # Mengambil package target dari konfigurasi saat ini
    active_pkg = config_mgr.config_data.get("package", "None (Go to Menu 2)")
    
    # Catatan: Jumlah terdeteksi disetel konstan/dinamis menyesuaikan performa list
    console.print("\n[bold magenta]Detected Packages:[/bold magenta] [yellow]Active Scanning Available[/yellow]")
    console.print(f"[bold green]Current Target App:[/bold green] [white]{active_pkg}[/white]\n")
