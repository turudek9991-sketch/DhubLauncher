#!/data/data/com.termux/files/usr/bin/bash
# ------------------------------------------------------------------
# DHub-Rejoin - Automated Installer Script for Termux
# ------------------------------------------------------------------

# Reset warna terminal
NC='\033[0m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'

echo -e "${CYAN}==================================================${NC}"
echo -e "${GREEN}          DHub-Rejoin Installer for Termux         ${NC}"
echo -e "${CYAN}==================================================${NC}"

# 1. Update & Upgrade Repositori Termux
echo -e "\n${YELLOW}[*] Memperbarui package repository Termux...${NC}"
pkg update -y && pkg upgrade -y

# 2. Install Python dan dependensi sistem yang dibutuhkan
echo -e "\n${YELLOW}[*] Menginstal Python 3 dan termux-api...${NC}"
pkg install python -y
pkg install termux-api -y

# 3. Upgrade PIP ke versi terbaru
echo -e "\n${YELLOW}[*] Memperbarui PIP (Python Package Installer)...${NC}"
pip install --upgrade pip

# 4. Install Python Packages dari requirements.txt
if [ -f "requirements.txt" ]; then
    echo -e "\n${YELLOW}[*] Menginstal pustaka Python dari requirements.txt...${NC}"
    pip install -r requirements.txt
else
    echo -e "\n${RED}[!] File requirements.txt tidak ditemukan! Menginstal manual...${NC}"
    pip install rich colorama tabulate requests
fi

# 5. Membuat struktur folder tambahan jika belum ada
echo -e "\n${YELLOW}[*] Menyiapkan direktori log aplikasi...${NC}"
mkdir -p logs

# 6. Mengatur izin eksekusi script utama
echo -e "${YELLOW}[*] Mengatur izin eksekusi file...${NC}"
chmod +x main.py

echo -e "\n${GREEN}[+] Instalasi selesai berhasil!${NC}"
echo -e "${CYAN}Gunakan perintah '${YELLOW}python main.py${CYAN}' untuk menjalankan aplikasi.${NC}"
echo -e "${CYAN}==================================================${NC}"
