import asyncio
import sys
import re
import datetime
import os
import requests
from textwrap import dedent

from googleapiclient.discovery import build
from google.oauth2 import service_account
from telegram import Bot

# ====================================================
# WARNA TERMINAL
# ====================================================
YELLOW = "\033[93m"
WHITE = "\033[97m"
CYAN = "\033[96m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# ====================================================
# FUNGSI BACA FILE DAN EKSTRAK SPREADSHEET ID
# ====================================================
def read_file(filename):
    try:
        with open(filename, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"{YELLOW}❌ Gagal membaca {filename}: {e}{RESET}")
        return None

def extract_spreadsheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    return match.group(1) if match else None

# ====================================================
# INISIALISASI GOOGLE SHEETS API
# ====================================================
# Inisialisasi Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Dapatkan direktori script saat ini (misal: DROPXJUNGLER/reshareshing)
script_dir = os.path.dirname(os.path.realpath(_file_))

# Dapatkan direktori induk, yaitu folder DROPXJUNGLER
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

# Susun path lengkap ke file credentials.json di folder induk
credentials_path = os.path.join(parent_dir, 'credentials.json')

# Muat kredensial dari file di folder induk
creds = service_account.Credentials.from_service_account_file(
    credentials_path, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=creds)
# ====================================================
# KONFIGURASI BAGIAN MODERATOR
# ====================================================
SHEET1_NAME = "Reshareshing"   # Link 1
SHEET2_NAME = "Analysis"        # Link 2
SHEET3_NAME = "Strategy"        # Link 3

telegram_token = read_file("Token.txt")
telegram_chat_id = read_file("Idchat.txt")
moderator_spreadsheet_id = extract_spreadsheet_id(read_file("Linkgsmoderator.txt"))

with open("Linkgs.txt", "r") as f:
    links = [line.strip() for line in f if line.strip()]
if len(links) < 3:
    raise ValueError("Linkgs.txt harus berisi 3 URL")
link1, link2, link3 = links[:3]

# Fungsi mengambil data dari cell tertentu
def get_cell_data(url, cell, sheet_name):
    ss_id = extract_spreadsheet_id(url)
    range_name = f"{sheet_name}!{cell}"
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=ss_id,
            range=range_name
        ).execute()
        return result.get('values', [[None]])[0][0] or ""
    except Exception as e:
        print(f"{YELLOW}ERROR: Gagal baca {range_name} dari {url}{RESET}")
        return ""

# Mencari baris sumber berikutnya (baris genap yang belum bertanda "OK")
def get_next_common_source_row():
    row = 2
    while True:
        if row % 2 != 0:
            row += 1
            continue
        flag1 = get_cell_data(link1, f"Z{row}", SHEET1_NAME).strip().upper()
        flag2 = get_cell_data(link2, f"Z{row}", SHEET2_NAME).strip().upper()
        flag3 = get_cell_data(link3, f"Z{row}", SHEET3_NAME).strip().upper()
        if flag1 == "OK" or flag2 == "OK" or flag3 == "OK":
            row += 2  # lompat ke baris genap berikutnya
        else:
            return row

# Menentukan baris moderator berikutnya
def get_next_moderator_row():
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=moderator_spreadsheet_id,
        range="A:A"
    ).execute()
    values = result.get('values', [])
    last_row = len(values) if values else 0
    if last_row < 2:
        return 2
    return last_row + 2 if last_row % 2 == 0 else last_row + 1

# Mengumpulkan data dari ketiga sumber menggunakan baris yang sama
def collect_data(row_suffix):
    return {
        'proyek': get_cell_data(link1, f"B{row_suffix}", SHEET1_NAME),
        'situs': get_cell_data(link1, f"C{row_suffix}", SHEET1_NAME),
        'roadmap': get_cell_data(link1, f"D{row_suffix}", SHEET1_NAME),
        'faucet': get_cell_data(link1, f"F{row_suffix}", SHEET1_NAME),
        'block_explorer': get_cell_data(link1, f"H{row_suffix}", SHEET1_NAME),
        'funding': get_cell_data(link1, f"G{row_suffix}", SHEET1_NAME) or input("Funding (manual input): "),
        'jenis_airdrop': get_cell_data(link2, f"C{row_suffix}", SHEET2_NAME),
        'rating': get_cell_data(link2, f"E{row_suffix}", SHEET2_NAME),
        'step_by_step': get_cell_data(link3, f"C{row_suffix}", SHEET3_NAME)
    }

# ====================================================
# FUNGSI BAGIAN MODERATOR (OPSI 1)
# ====================================================
async def proses_moderator():
    source_row = get_next_common_source_row()
    moderator_row = get_next_moderator_row()
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    data = collect_data(source_row)
    
    print(f"\n{YELLOW}=== DATA YANG AKAN DISIMPAN ==={RESET}")
    for key, value in data.items():
        print(f"{key.upper():<15}: {value}")
    
    feedback = input(f"\n{YELLOW}Masukkan FEEDBACK (manual): {RESET}")
    
    if input(f"\n{YELLOW}Apakah anda yakin (y/n)? {RESET}").lower() != 'y':
        print(f"{YELLOW}Dibatalkan!{RESET}")
        return
    
    moderator_header = ["TIMESTAMP", "PROYEK", "SITUS", "ROADMAP", "FAUCET",
          "BLOCK_EXPLORER", "FUNDING", "JENIS_AIRDROP", "RATING", "STEP_BY_STEP", "FEEDBACK"] + [""]*13
    
    if moderator_row == 2:
        sheets_service.spreadsheets().values().update(
            spreadsheetId=moderator_spreadsheet_id,
            range="A1:Y1",
            valueInputOption="RAW",
            body={"values": [moderator_header]}
        ).execute()
    
    moderator_row_data = [
        timestamp,
        data['proyek'],
        data['situs'],
        data['roadmap'],
        data['faucet'],
        data['block_explorer'],
        data['funding'],
        data['jenis_airdrop'],
        data['rating'],
        data['step_by_step'],
        feedback
    ] + [""]*13 + ["M"]
    
    body = {"values": [moderator_row_data]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=moderator_spreadsheet_id,
        range=f"A{moderator_row}:Y{moderator_row}",
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    
    print(f"{YELLOW}Data tersimpan di spreadsheet moderator.{RESET}")
    
    # Tandai baris sumber dengan "OK"
    for url, sheet in [(link1, SHEET1_NAME), (link2, SHEET2_NAME), (link3, SHEET3_NAME)]:
        ss_id = extract_spreadsheet_id(url)
        range_to_update = f"{sheet}!Z{source_row}"
        sheets_service.spreadsheets().values().update(
             spreadsheetId=ss_id,
             range=range_to_update,
             valueInputOption="RAW",
             body={'values': [["OK"]]}
        ).execute()
    
    async def send_notification():
        message = (
            f"📋 **AIRDROP BARU**\n"
            f"🕒 Timestamp: `{timestamp}`\n"
            f"🏆 Airdrop: `{data['proyek']}`\n"
            f"🌐 Situs: {data['situs']}\n"
            f"⭐ Rating: {data['rating']}\n"
            f"🔗 Full Data: {read_file('Linkgsmoderator.txt')}\n"
            f"🔗 Info script: https://docs.google.com/spreadsheets/d/1b-8hDUKd3hWy2qEVopwFr663c8vbUQmBZoVnyQYjg0Q/edit?gid=0#gid=0"
        )
        await Bot(telegram_token).send_message(
            chat_id=telegram_chat_id,
            text=message,
            parse_mode="Markdown"
        )
    
    await send_notification()
    print(f"\n{YELLOW}✅ Data tersimpan dan notifikasi terkirim!{RESET}")

# ====================================================
# BAGIAN LIST AIRDROP (OPSI 2)
# ====================================================
list_airdrop_spreadsheet_id = extract_spreadsheet_id(read_file("Linkgslistairdrop.txt"))
MODERATOR_SHEET = "Moderator"
LIST_SHEET = "listairdrop"

def get_moderator_data():
    range_name = f"{MODERATOR_SHEET}!A2:K"
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=moderator_spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get("values", [])
    return values

def group_airdrop_data(rows):
    groups = {
        "TESTNET": [],
        "WEB3": [],
        "EXTENSION": [],
        "APLIKASI": [],
        "NODE TESTNET": [],
        "ROLE DISCORD": []
    }
    for row in rows:
        if len(row) < 8:
            continue
        situs = row[2].strip() if row[2] else ""
        jenis = row[7].strip().upper() if row[7] else ""
        if situs and jenis in groups:
            groups[jenis].append(situs)
    return groups

def group_check_in_data(rows):
    valid_keywords = {"bridge", "delegasi", "faucet", "mint nft", "deploy",
                      "staking", "supply and borrow", "trade", "check in", "swap"}
    check_in_sites = []
    for row in rows:
        if len(row) < 10:
            continue
        step_text = row[9].lower()
        if any(keyword in step_text for keyword in valid_keywords):
            situs = row[2].strip() if len(row) > 2 and row[2] else ""
            if situs:
                check_in_sites.append(situs)
    return check_in_sites

async def update_list_airdrop_sheet(groups, check_in_list):
    header_list = ["Testnet", "Web3", "Extension", "Aplikasi", "Node testnet", "Role discord", "", "", "Check in"]
    header_range = f"{LIST_SHEET}!A1:I1"
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=list_airdrop_spreadsheet_id,
        range=header_range
    ).execute()
    values = result.get("values", [])
    if not values or values[0] != header_list:
        body = {"values": [header_list]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=list_airdrop_spreadsheet_id,
            range=header_range,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        print(f"{YELLOW}Header list airdrop berhasil ditulis di {header_range}.{RESET}")
    
    col_mapping = {
        "TESTNET": "A",
        "WEB3": "B",
        "EXTENSION": "C",
        "APLIKASI": "D",
        "NODE TESTNET": "E",
        "ROLE DISCORD": "F"
    }
    
    for kategori, situs_list in groups.items():
        col_letter = col_mapping.get(kategori)
        if not col_letter:
            continue
        unique_list = list(dict.fromkeys(situs_list))
        update_range = f"{LIST_SHEET}!{col_letter}2:{col_letter}{len(unique_list)+1}"
        new_values = [[s] for s in unique_list]
        body = {"values": new_values}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=list_airdrop_spreadsheet_id,
            range=update_range,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        print(f"{YELLOW}Data untuk kategori {kategori} berhasil diperbarui (tidak duplikat) di {update_range}.{RESET}")
    
    # Update kolom I untuk "Check in"
    col_letter = "I"
    unique_check_in_list = list(dict.fromkeys(check_in_list))
    update_range = f"{LIST_SHEET}!{col_letter}2:{col_letter}{len(unique_check_in_list)+1}"
    new_values = [[s] for s in unique_check_in_list]
    body = {"values": new_values}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=list_airdrop_spreadsheet_id,
        range=update_range,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    print(f"{YELLOW}Data untuk kategori Check in berhasil diperbarui (tidak duplikat) di {update_range}.{RESET}")
    
    # Tambahkan marker "M" di kolom Y
    marker_range = f"{LIST_SHEET}!Y2:Y"
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=list_airdrop_spreadsheet_id,
        range=marker_range
    ).execute()
    existing_markers = result.get("values", [])
    next_marker_row = len(existing_markers) + 2
    update_marker_range = f"{LIST_SHEET}!Y{next_marker_row}"
    body = {"values": [["M"]]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=list_airdrop_spreadsheet_id,
        range=update_marker_range,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    print(f"{YELLOW}Marker 'M' berhasil ditambahkan di {update_marker_range}.{RESET}")

async def send_notification_list(groups, check_in_list):
    summary_lines = ["*List Data Airdrop Mingguan:*"]
    for kategori, situs_list in groups.items():
        if situs_list:
            unique_list = list(dict.fromkeys(situs_list))
            summary_lines.append(f"*{kategori.title()}*: {', '.join(unique_list)}")
        else:
            summary_lines.append(f"*{kategori.title()}*: 0 situs")
    unique_check_in_list = list(dict.fromkeys(check_in_list))
    summary_lines.append(f"*Check in*: {', '.join(unique_check_in_list) if unique_check_in_list else '0 situs'}")
    message = "\n".join(summary_lines)
    await Bot(telegram_token).send_message(
        chat_id=telegram_chat_id,
        text=message,
        parse_mode="Markdown"
    )
    print(f"{YELLOW}Notifikasi Telegram terkirim.{RESET}")

async def update_list():
    print(f"\n{YELLOW}=== PROSES LIST DATA AIRDROP ==={RESET}")
    rows = get_moderator_data()
    if not rows:
        print(f"{YELLOW}Tidak ada data di moderator.{RESET}")
        return
    groups = group_airdrop_data(rows)
    check_in_list = group_check_in_data(rows)
    await update_list_airdrop_sheet(groups, check_in_list)
    await send_notification_list(groups, check_in_list)
    print(f"\n{YELLOW}✅ Proses list data airdrop selesai.{RESET}")
    print(f"{YELLOW}Catatan: Script ini dijadwalkan untuk dijalankan sekali seminggu (gunakan cron atau scheduler lainnya).{RESET}")

# ====================================================
# MENU UTAMA
# ====================================================
def tampilkan_menu():
    print(dedent(f"""
    {WHITE}
██████  ██████   ██████  ██████  ██   ██      ██ ██    ██ ███    ██  ██████  ██      ███████ ██████      
██   ██ ██   ██ ██    ██ ██   ██  ██ ██       ██ ██    ██ ████   ██ ██       ██      ██      ██   ██     
██   ██ ██████  ██    ██ ██████    ███        ██ ██    ██ ██ ██  ██ ██   ███ ██      █████   ██████      
██   ██ ██   ██ ██    ██ ██       ██ ██  ██   ██ ██    ██ ██  ██ ██ ██    ██ ██      ██      ██   ██     
██████  ██   ██  ██████  ██      ██   ██  █████   ██████  ██   ████  ██████  ███████ ███████ ██   ██     
                                                                                                         
                                           MODERATOR TOOLS                                                                
    {RESET}
    {YELLOW}1.{RESET} Input Data Moderator
    {YELLOW}2.{RESET} Update List Airdrop
    {YELLOW}3.{RESET} Keluar
    """))

async def jalankan_moderator():
    try:
        await proses_moderator()
    except Exception as e:
        print(f"{RED}❌ Gagal menjalankan Moderator: {str(e)}{RESET}")
    finally:
        input("\nTekan Enter untuk kembali ke menu...")

async def jalankan_list():
    try:
        await update_list()
    except Exception as e:
        print(f"{RED}❌ Gagal menjalankan List Airdrop: {str(e)}{RESET}")
    finally:
        input("\nTekan Enter untuk kembali ke menu...")

async def main_menu():
    while True:
        tampilkan_menu()
        pilihan = input(f"{YELLOW}➤ Pilih opsi (1-3): {RESET}").strip()
        if pilihan == "1":
            await jalankan_moderator()
        elif pilihan == "2":
            await jalankan_list()
        elif pilihan == "3":
            print(f"{GREEN}👋 Sampai jumpa!{RESET}")
            sys.exit()
        else:
            print(f"{RED}⚠ Pilihan tidak valid!{RESET}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        print(f"\n{RED}🚫 Program dihentikan paksa!{RESET}")
    except Exception as e:
        print(f"{RED}💥 Error tidak terduga: {str(e)}{RESET}")
