import re
import datetime
import os
import asyncio
from googleapiclient.discovery import build
from google.oauth2 import service_account
from telegram import Bot

# Warna output terminal
WHITE = "\033[97m"
PURPLE = "\033[95m"
RESET = "\033[0m"

########################################
# LOGO
########################################

logo = r"""
██████  ██████   ██████  ██████  ██   ██      ██ ██    ██ ███    ██  ██████  ██      ███████ ██████      
██   ██ ██   ██ ██    ██ ██   ██  ██ ██       ██ ██    ██ ████   ██ ██       ██      ██      ██   ██     
██   ██ ██████  ██    ██ ██████    ███        ██ ██    ██ ██ ██  ██ ██   ███ ██      █████   ██████         
██   ██ ██   ██ ██    ██ ██       ██ ██  ██   ██ ██    ██ ██  ██ ██ ██    ██ ██      ██      ██   ██     
██████  ██   ██  ██████  ██      ██   ██  █████   ██████  ██   ████  ██████  ███████ ███████ ██   ██     
                                                                                                       
                                         MONITORING  TOOLS  
"""

# Cetak logo dengan warna putih
print(WHITE + logo + RESET)

########################################
# UTILITAS
########################################

def read_file(filename):
    """Baca file dan kembalikan isinya (strip spasi)."""
    try:
        with open(filename, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"{PURPLE}❌ Gagal membaca {filename}: {e}{RESET}")
        return None

def parse_spreadsheet_ids(filename):
    """Parse spreadsheet IDs dari file."""
    content = read_file(filename)
    ids = {}
    if content:
        for line in content.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                ids[key.strip()] = val.strip()
    return ids

########################################
# KONFIGURASI
########################################

spreadsheet_ids = parse_spreadsheet_ids("mospreadsheet_id.txt")

daily_categories   = ["Reshareshing", "Analysis", "Strategy", "Moderator", "Dimas", "Agung", "Anang", "Tayong", "Agus", "Frendi", "Ulan"]
weekly_categories  = ["listairdrop"]
monthly_categories = ["Datacurator"]

if "listairdrop" not in spreadsheet_ids and "Moderator" in spreadsheet_ids:
    spreadsheet_ids["listairdrop"] = spreadsheet_ids["Moderator"]

sheet_names = {
    "Reshareshing": "Reshareshing",
    "Analysis": "Analysis",
    "Strategy": "Strategy",
    "Moderator": "Moderator",
    "listairdrop": "listairdrop",
    "Datacurator": "Datacurator"
}

marker_columns = {"Datacurator": "AY"}

monitoring_header = [
    "Timestamp", "Reshareshing", "Analysis", "Strategy", "Moderator", "ListAirdrop",
    "Dimas", "Agung", "Anang", "Tayong", "Agus", "Frendi", "Ulan", "Datacurator"
]

monitoring_id = read_file("monitoringid.txt")
telegram_token = read_file("Token.txt")
telegram_chat_id = read_file("Idchat.txt")
threads_text = read_file("Threads.txt")
thread_ids = [int(line.strip()) for line in threads_text.splitlines()] if threads_text else None

########################################
# GOOGLE SHEETS API
########################################

# Inisialisasi Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Dapatkan direktori script saat ini (misal: DROPXJUNGLER/reshareshing)
script_dir = os.path.dirname(os.path.realpath(__file__))

# Dapatkan direktori induk, yaitu folder DROPXJUNGLER
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

# Susun path lengkap ke file credentials.json di folder induk
credentials_path = os.path.join(parent_dir, 'credentials.json')

# Muat kredensial dari file di folder induk
creds = service_account.Credentials.from_service_account_file(
    credentials_path, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=creds)

########################################
# HEADER MANAGEMENT
########################################

def ensure_monitoring_header():
    """Pastikan header Monitoring ada."""
    header_range = "Monitoring!A1:O1"
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=monitoring_id,
            range=header_range,
            majorDimension="ROWS"
        ).execute()
        values = result.get("values", [])
        if values and values[0][0] == "Timestamp":
            return
    except Exception as e:
        print(f"{PURPLE}❌ Gagal memeriksa header: {e}{RESET}")
    
    body = {"values": [monitoring_header]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=monitoring_id,
        range=header_range,
        valueInputOption="USER_ENTERED",
        body=body
    ).execute()
    print(f"{PURPLE}📝 Header Monitoring telah dipastikan{RESET}")

########################################
# MONITORING FUNCTIONS
########################################

def count_marker(sheet_id, sheet_name, marker_col="Y"):
    """Hitung 'M' di kolom marker."""
    range_name = f"{sheet_name}!{marker_col}2:{marker_col}"
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        return sum(1 for row in result.get("values", []) if row and row[0].strip().upper() == "M")
    except Exception as e:
        print(f"{PURPLE}❌ Gagal menghitung marker di {sheet_name}: {e}{RESET}")
        return 0

def monitor_categories(categories):
    """Hitung interaksi per kategori."""
    results = {}
    for cat in categories:
        if cat in sheet_names:
            sheet_id = spreadsheet_ids.get(cat)
            s_name = sheet_names.get(cat, "Sheet1")
            marker_col = marker_columns.get(cat, "Y")
            results[cat] = count_marker(sheet_id, s_name, marker_col) if sheet_id else 0
        else:
            sheet_id = spreadsheet_ids.get(cat)
            results[cat] = count_marker(sheet_id, cat, "Y") if sheet_id else 0
    return results

########################################
# TOTAL CALCULATION & DATA CLEANUP
########################################

def calculate_total_monitoring():
    """Hitung total dari semua data mentah."""
    range_name = "Monitoring!A2:O"
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=monitoring_id,
            range=range_name,
            majorDimension="ROWS"
        ).execute()
        rows = result.get('values', [])
    except Exception as e:
        print(f"{PURPLE}❌ Gagal mengambil data: {e}{RESET}")
        return {}

    totals = {category: 0 for category in [
        "Reshareshing", "Analysis", "Strategy", "Moderator",
        "listairdrop", "Dimas", "Agung", "Anang",
        "Tayong", "Agus", "Frendi", "Ulan", "Datacurator"
    ]}

    for row in rows:
        totals["Reshareshing"] += int(row[1]) if len(row) > 1 and row[1] else 0
        totals["Analysis"] += int(row[2]) if len(row) > 2 and row[2] else 0
        totals["Strategy"] += int(row[3]) if len(row) > 3 and row[3] else 0
        totals["Moderator"] += int(row[4]) if len(row) > 4 and row[4] else 0
        totals["listairdrop"] += int(row[5]) if len(row) > 5 and row[5] else 0
        totals["Dimas"] += int(row[6]) if len(row) > 6 and row[6] else 0
        totals["Agung"] += int(row[7]) if len(row) > 7 and row[7] else 0
        totals["Anang"] += int(row[8]) if len(row) > 8 and row[8] else 0
        totals["Tayong"] += int(row[9]) if len(row) > 9 and row[9] else 0
        totals["Agus"] += int(row[10]) if len(row) > 10 and row[10] else 0
        totals["Frendi"] += int(row[11]) if len(row) > 11 and row[11] else 0
        totals["Ulan"] += int(row[12]) if len(row) > 12 and row[12] else 0
        totals["Datacurator"] += int(row[13]) if len(row) > 13 and row[13] else 0

    return totals

def delete_data_rows(num_rows):
    """Hapus data mentah setelah dihitung total."""
    try:
        sheet_info = sheets_service.spreadsheets().get(spreadsheetId=monitoring_id).execute()
        monitoring_sheet_id = None
        for sheet in sheet_info['sheets']:
            if sheet['properties']['title'] == 'Monitoring':
                monitoring_sheet_id = sheet['properties']['sheetId']
                break
        
        if monitoring_sheet_id is None:
            print(f"{PURPLE}❌ Sheet 'Monitoring' tidak ditemukan{RESET}")
            return

        requests = {
            "requests": [{
                "deleteDimension": {
                    "range": {
                        "sheetId": monitoring_sheet_id,
                        "dimension": "ROWS",
                        "startIndex": 1,
                        "endIndex": 1 + num_rows
                    }
                }
            }]
        }
        
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=monitoring_id,
            body=requests
        ).execute()
        
        print(f"{PURPLE}🗑️ Menghapus {num_rows} baris data mentah{RESET}")
    except Exception as e:
        print(f"{PURPLE}❌ Gagal menghapus data: {e}{RESET}")

########################################
# SAVE & NOTIFY
########################################

def save_monitoring_results(results, period):
    """Simpan hasil ke sheet Monitoring."""
    ensure_monitoring_header()
    
    # Format timestamp: jam:menit:detik tanggal/bulan/tahun
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    row = [timestamp] + [results.get(cat, 0) for cat in [
        "Reshareshing", "Analysis", "Strategy", "Moderator", "listairdrop",
        "Dimas", "Agung", "Anang", "Tayong", "Agus", "Frendi", "Ulan", "Datacurator"
    ]]
    
    sheets_service.spreadsheets().values().append(
        spreadsheetId=monitoring_id,
        range="Monitoring!A2",
        valueInputOption="USER_ENTERED",
        body={"values": [row]}
    ).execute()
    print(f"{PURPLE}💾 Hasil {period} telah disimpan ke sheet Monitoring{RESET}")

def mark_monitoring(period):
    """Tambah satu 'M' di kolom Z untuk total."""
    sheets_service.spreadsheets().values().append(
        spreadsheetId=monitoring_id,
        range="Monitoring!Z:Z",
        valueInputOption="USER_ENTERED",
        body={"values": [["M"]]}
    ).execute()
    print(f"{PURPLE}🔖 Marker untuk {period} telah ditambahkan{RESET}")

async def send_monitoring_notification(results, period):
    """Kirim notifikasi Telegram."""
    summary = [f"*📊 HASIL MONITORING {period.upper()}*"]
    for cat in [
        "Reshareshing", "Analysis", "Strategy", "Moderator", "listairdrop",
        "Dimas", "Agung", "Anang", "Tayong", "Agus", "Frendi", "Ulan", "Datacurator"
    ]:
        summary.append(f"▫️ *{cat}*: {results.get(cat, 0)}")
    
    bot = Bot(telegram_token)
    message = "\n".join(summary)
    
    if thread_ids:
        for tid in thread_ids:
            await bot.send_message(
                chat_id=telegram_chat_id,
                text=message,
                parse_mode="Markdown",
                message_thread_id=tid
            )
    else:
        await bot.send_message(
            chat_id=telegram_chat_id,
            text=message,
            parse_mode="Markdown"
        )
    print(f"{PURPLE}✅ Notifikasi {period} telah dikirim ke Telegram{RESET}")

########################################
# MAIN MENU
########################################

def run_total_monitoring():
    """Jalankan monitoring total dan bersihkan data mentah."""
    print(f"{PURPLE}🔄 Memproses total...{RESET}")
    
    # Hitung jumlah data mentah
    range_name = "Monitoring!A2:O"
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=monitoring_id,
        range=range_name,
        majorDimension="ROWS"
    ).execute()
    num_data_rows = len(result.get('values', []))
    
    # Hitung total
    totals = calculate_total_monitoring()
    print(f"{PURPLE}📊 Total hasil monitoring: {totals}{RESET}")
    
    # Simpan total
    save_monitoring_results(totals, "TOTAL")
    
    # Hapus data mentah
    if num_data_rows > 0:
        delete_data_rows(num_data_rows)
    
    # Tambah marker
    mark_monitoring("TOTAL")
    
    # Kirim notifikasi
    asyncio.run(send_monitoring_notification(totals, "TOTAL"))
    
    print(f"{PURPLE}✅ Total berhasil dihitung dan data dibersihkan{RESET}")

def menu():
    while True:
        print(f"""{PURPLE}
[1] Monitoring Harian
[2] Monitoring Mingguan
[3] Monitoring Bulanan
[4] TOTAL SEMUA DATA
[5] Keluar
{RESET}""")
        choice = input(f"{PURPLE}Pilih opsi: {RESET}")
        
        if choice == "1":
            results = monitor_categories(daily_categories)
            print(f"{PURPLE}📊 Hasil Monitoring Harian: {results}{RESET}")
            save_monitoring_results(results, "Harian")
            asyncio.run(send_monitoring_notification(results, "Harian"))
            print(f"{PURPLE}✅ Monitoring Harian selesai dan notifikasi dikirim{RESET}")
        elif choice == "2":
            results = monitor_categories(weekly_categories)
            print(f"{PURPLE}📊 Hasil Monitoring Mingguan: {results}{RESET}")
            save_monitoring_results(results, "Mingguan")
            asyncio.run(send_monitoring_notification(results, "Mingguan"))
            print(f"{PURPLE}✅ Monitoring Mingguan selesai dan notifikasi dikirim{RESET}")
        elif choice == "3":
            results = monitor_categories(monthly_categories)
            print(f"{PURPLE}📊 Hasil Monitoring Bulanan: {results}{RESET}")
            save_monitoring_results(results, "Bulanan")
            asyncio.run(send_monitoring_notification(results, "Bulanan"))
            print(f"{PURPLE}✅ Monitoring Bulanan selesai dan notifikasi dikirim{RESET}")
        elif choice == "4":
            run_total_monitoring()
        elif choice == "5":
            print(f"{PURPLE}🔚 Program selesai.{RESET}")
            break
        else:
            print(f"{PURPLE}❌ Pilihan tidak valid! Silakan coba lagi.{RESET}")
            
if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        # Saat Ctrl+C ditekan, tampilkan pesan dan hentikan program tanpa traceback error
        print(f"\n{PURPLE}Program dihentikan oleh pengguna.{RESET}")
