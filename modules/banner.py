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
    Menampilkan banner utama DHub-Rejoin secara simetris dan rapi.
    """
    console.clear()
    
    # Text-art banner gaya futuristik
    banner_text = (
        "[bold cyan]██████╗ ██╗  ██╗██╗   ██╗██████╗ \n"
        "██╔══██╗██║  ██║██║   ██║██╔══██╗\n"
        "██║  ██║███████║██║   ██║██████╔╝\n"
        "██║  ██║██╔══██║██║   ██║██╔══██╗\n"
        "██████╔╝██║  ██║╚██████╔╝██████╔╝\n"
        "╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ [/bold cyan]\n"
        "[dim white]=========================================[/dim white]\n"
        "          [bold green]DHub Launcher Engine[/bold green]          \n"
        "             Version 1.0.0               \n"
        "[dim white]=========================================[/dim white]"
    )
    
    console.print(banner_text)
    
    # Mengambil package target aktif dari config
    active_pkg = config_mgr.config_data.get("package", "None (Run Package Manager)")
    
    console.print("\n[bold magenta]» Monitoring Status app:[/bold magenta]")
    console.print(f"  Target Active : [yellow]{active_pkg}[/yellow]\n")
