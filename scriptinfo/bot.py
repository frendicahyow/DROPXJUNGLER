import re
import datetime
import requests
import os
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Warna terminal
BLUE = "\033[94m"
WHITE = "\033[97m"
RESET = "\033[0m"

########################################
# FUNGSI UNTUK MENAMPILKAN LOGO
########################################
def tampilkan_logo():
    logo = f"""{WHITE}
██████  ██████   ██████  ██████  ██   ██      ██ ██    ██ ███    ██  ██████  ██      ███████ ██████      
██   ██ ██   ██ ██    ██ ██   ██  ██ ██       ██ ██    ██ ████   ██ ██       ██      ██      ██   ██     
██   ██ ██████  ██    ██ ██████    ███        ██ ██    ██ ██ ██  ██ ██   ███ ██      █████   ██████         
██   ██ ██   ██ ██    ██ ██       ██ ██  ██   ██ ██    ██ ██  ██ ██ ██    ██ ██      ██      ██   ██     
██████  ██   ██  ██████  ██      ██   ██  █████   ██████  ██   ████  ██████  ███████ ███████ ██   ██     

                                           SCRIPT TOOLS  
{RESET}"""
    print(logo)

########################################
# UTILITAS
########################################
def read_file(filename):
    """Baca file dan kembalikan isinya (strip spasi)."""
    if not os.path.exists(filename):
        print(f"{BLUE}❌ File {filename} tidak ditemukan.{RESET}")
        return None
    try:
        with open(filename, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f"{BLUE}❌ Gagal membaca {filename}: {e}{RESET}")
        return None

def extract_spreadsheet_id(link):
    match = re.search(r'/d/([a-zA-Z0-9-_]+)', link)
    return match.group(1) if match else link.strip()

def load_config():
    try:
        with open('token.txt', 'r') as f:
            telegram_token = f.read().strip()
        with open('idchat.txt', 'r') as f:
            telegram_chat_id = f.read().strip()
        with open('linkgs.txt', 'r') as f:
            spreadsheet_id = extract_spreadsheet_id(f.read().strip())
        with open('threads.txt', 'r') as f:
            thread_text = f.read().strip()
            thread_id = int(thread_text) if thread_text.isdigit() else None
    except Exception as e:
        print(f"{BLUE}❌ Gagal memuat konfigurasi: {e}{RESET}")
        telegram_token, telegram_chat_id, spreadsheet_id, thread_id = None, None, None, None
    return telegram_token, telegram_chat_id, spreadsheet_id, thread_id

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, SPREADSHEET_ID, THREAD_ID = load_config()

########################################
# TELEGRAM PENGIRIMAN
########################################
def send_to_telegram(message, thread_id=None):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"{BLUE}❌ Token atau Chat ID Telegram tidak ditemukan.{RESET}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    if thread_id is not None:
        payload["message_thread_id"] = thread_id
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"{BLUE}✅ Data berhasil dikirim ke Telegram.{RESET}")
        else:
            print(f"{BLUE}❌ Gagal mengirim data ke Telegram: {response.text}{RESET}")
    except Exception as e:
        print(f"{BLUE}❌ Kesalahan saat mengirim ke Telegram: {e}{RESET}")

########################################
# GOOGLE SHEETS PENGIRIMAN
########################################
def build_sheets_service():
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
    return build('sheets', 'v4', credentials=creds)

def send_to_sheets(record, sheet_name):
    """
    Mengirim data ke Google Sheets.
    record: list dengan 3 elemen [Timestamp, Nama Script, Link GitHub].
    Data baru ditulis pada baris genap (misalnya, A2:C2, A4:C4, dst.)
    Marker "M" ditambahkan di kolom Y.
    """
    if not SPREADSHEET_ID:
        print(f"{BLUE}❌ Spreadsheet ID tidak ditemukan.{RESET}")
        return

    service = build_sheets_service()
    sheet = service.spreadsheets()

    # Header disesuaikan dengan 3 kolom
    header_list = ["timestamp", "nama script", "linkgithub"]
    header_range = f"Script!A1:C1"
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=header_range).execute()
    values = result.get("values", [])
    if not values or values[0] != header_list:
        body = {"values": [header_list]}
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=header_range,
            valueInputOption="RAW",
            body=body
        ).execute()
        print(f"{BLUE}Header berhasil ditulis di {header_range}.{RESET}")
        data_count = 0
    else:
        # Hitung jumlah baris data di kolom A (mulai dari baris 2)
        data_range = f"Script!A2:A"
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=data_range).execute()
        values = result.get("values", [])
        data_count = len([row for row in values if row and row[0].strip() != ""])

    # Tentukan baris berikutnya (baris genap)
    next_data_row = 2 * (data_count + 1)
    update_range = f"Script!A{next_data_row}:C{next_data_row}"
    body_data = {"values": [record]}
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=update_range,
        valueInputOption="RAW",
        body=body_data
    ).execute()
    print(f"{BLUE}Data berhasil ditulis di {update_range}.{RESET}")

    # Tambahkan marker "M" di kolom Y pada baris yang sama
    marker_range = f"Script!Y{next_data_row}:Y{next_data_row}"
    body_marker = {"values": [["M"]]}
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=marker_range,
        valueInputOption="RAW",
        body=body_marker
    ).execute()
    print(f"{BLUE}Marker 'M' berhasil ditambahkan di {marker_range}.{RESET}")

########################################
# NOTIFIKASI TELEGRAM DENGAN LINK SPREADSHEET
########################################
def notify_update():
    if not SPREADSHEET_ID:
        print(f"{BLUE}❌ Spreadsheet ID tidak ditemukan untuk mengirim notifikasi.{RESET}")
        return
    # Buat link lengkap ke spreadsheet
    spreadsheet_link = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    message = f"Siap sabar bolo, link spreadsheet: <a href='{spreadsheet_link}'>Klik di sini</a>"
    send_to_telegram(message, THREAD_ID)

########################################
# MAIN PROGRAM
########################################
def process_sheet():
    try:
        tampilkan_logo()
        script_name = input(f"{BLUE}Masukkan nama script: {RESET}").strip()
        if not script_name:
            print(f"{BLUE}❌ Nama script tidak boleh kosong.{RESET}")
            return
        github_link = input(f"{BLUE}Masukkan link GitHub: {RESET}").strip()
        if not github_link:
            print(f"{BLUE}❌ Link GitHub tidak boleh kosong.{RESET}")
            return
        now = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        record = [now, script_name, github_link]

        send_to_sheets(record, "Script")
        notify_update()

    except Exception as e:
        print(f"{BLUE}❌ ERROR: {str(e)}{RESET}")

if __name__ == '__main__':
    try:
        process_sheet()
    except KeyboardInterrupt:
        print(f"\n{BLUE}Program dihentikan oleh pengguna.{RESET}")
