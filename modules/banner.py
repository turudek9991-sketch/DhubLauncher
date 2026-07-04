"""
DHub-Rejoin - Banner Core Module (Integrated Multi-Target)
Author: Senior Python Developer
Description: Renders the primary application logo branding with dynamic active target lists.
"""

from rich.console import Console
import os

console = Console()

def show_banner(config_mgr, active_list="None"):
    """
    Menampilkan banner futuristik dengan daftar target aktif yang terdeteksi dinamis.
    """
    console.clear()
    
    # Text-art banner gaya futuristik
    banner_text = (
        "[bold cyan]██████╗ ██╗  ██╗██╗   ██╗██████╗ [/bold cyan]\n"
        "[bold cyan]██╔══██╗██║  ██║██║   ██║██╔══██╗[/bold cyan]\n"
        "[bold cyan]██║  ██║███████║██║   ██║██████╔╝[/bold cyan]\n"
        "[bold cyan]██║  ██║██╔══██║██║   ██║██╔══██╗[/bold cyan]\n"
        "[bold cyan]██████╔╝██║  ██║╚██████╔╝██████╔╝[/bold cyan]\n"
        "[bold cyan]╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ [/bold cyan]\n"
        "[dim white]=========================================[/dim white]\n"
        "         [bold green]DHub Launcher Engine[/bold green]          \n"
        "           Version 4.6 - Multi-Target          \n"
        "[dim white]=========================================[/dim white]"
    )
    
    console.print(banner_text)
    
    # Menampilkan daftar semua package yang sedang aktif secara dinamis
    console.print("\n[bold magenta]» Monitoring Status app:[/bold magenta]")
    console.print(f"  [bold white]Target Active : [/bold white][yellow]{active_list}[/yellow]\n")
