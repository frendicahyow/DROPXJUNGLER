import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests

# --- Fungsi Membaca File ---
def read_file(filename):
    with open(filename, 'r') as file:
        return file.read().strip()

# Baca konfigurasi dari file
SPREADSHEET_ID = read_file("proofworkid.txt")
TELEGRAM_BOT_TOKEN = read_file("token.txt")
TELEGRAM_CHAT_ID = read_file("idchat.txt")
THREAD_ID = read_file("threads.txt")  # Jika diperlukan

# Konfigurasi Google Sheets API dengan file credentials.json
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'credentials.json'
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

# --- Fungsi Membaca Nama Sheet dari namesheet.txt ---
def read_sheet_names(filename='namesheet.txt'):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

sheet_names = read_sheet_names()

# --- Mendapatkan Daftar Sheet yang Ada ---
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
existing_sheets = [sheet['properties']['title'] for sheet in sheet_metadata.get('sheets', [])]

# --- Fungsi Membuat Sheet Baru Jika Belum Ada ---
def create_sheet(sheet_name):
    request_body = {
        "requests": [
            {
                "addSheet": {
                    "properties": {
                        "title": sheet_name
                    }
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=request_body
    ).execute()
    print(f"Sheet '{sheet_name}' dibuat.")

# Cek dan buat sheet jika belum ada
for name in sheet_names:
    if name not in existing_sheets:
        create_sheet(name)

# --- Fungsi Memastikan Header Sudah Ada ---
def ensure_header(sheet_name):
    header_range = f"{sheet_name}!A1:E1"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range=header_range).execute()
    values = result.get('values', [])
    expected_header = ["Time stamp", "Name airdrop", "Jenis", "Akun", "feedback"]
    if not values or values[0] != expected_header:
        header = [expected_header]
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=header_range,
            valueInputOption="RAW",
            body={"values": header}
        ).execute()
        print(f"Header pada sheet '{sheet_name}' diatur ulang.")
    else:
        print(f"Header pada sheet '{sheet_name}' sudah ada.")

# Pastikan setiap sheet memiliki header yang benar
for name in sheet_names:
    ensure_header(name)

# --- Fungsi Menambahkan Data ke Sheet ---
def add_data(sheet_name, name_airdrop, jenis, akun_value, feedback_value):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data = [[timestamp, name_airdrop, jenis, akun_value, feedback_value]]
    
    # Menambahkan data ke baris berikutnya (misalnya mulai dari A2)
    range_append = f"{sheet_name}!A2"
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=range_append,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": data}
    ).execute()
    
    # Mendapatkan nomor baris terakhir dari kolom A (termasuk header)
    get_result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name}!A:A"
    ).execute()
    rows = get_result.get("values", [])
    last_row = len(rows)  # Header ada di baris 1
    
    # Menuliskan tanda "M" di kolom Y pada baris terakhir
    marker_range = f"{sheet_name}!Y{last_row}"
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=marker_range,
        valueInputOption="RAW",
        body={"values": [["M"]]}
    ).execute()
    print(f"Data dan marker 'M' pada sheet '{sheet_name}' telah diperbarui di baris {last_row}.")

# --- Memasukkan Data Secara Manual untuk Setiap Sheet ---
for name in sheet_names:
    print(f"\nMasukkan data untuk sheet '{name}':")
    name_airdrop = input("Ketikkan nilai untuk kolom Name airdrop: ")
    jenis = input("Ketikkan nilai untuk kolom Jenis: ")
    akun_input = input("Ketikkan nilai untuk kolom Akun: ")
    feedback_input = input("Ketikkan nilai untuk kolom feedback: ")
    add_data(name, name_airdrop, jenis, akun_input, feedback_input)

# --- Mengirim Notifikasi ke Telegram ---
message = "Data telah diperbarui di Google Sheet dan marker 'M' telah ditambahkan secara berurutan pada masing-masing sheet."
telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

response = requests.post(telegram_api_url, data=payload)
if response.status_code == 200:
    print("Notifikasi Telegram terkirim.")
else:
    print("Gagal mengirim notifikasi Telegram.")
