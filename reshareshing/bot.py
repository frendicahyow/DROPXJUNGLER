import os
import datetime
import asyncio
import telegram
from google.oauth2 import service_account
from googleapiclient.discovery import build
import nest_asyncio

# Terapkan nest_asyncio agar nested event loop bisa berjalan (cocok untuk lingkungan interaktif)
nest_asyncio.apply()

# ================================================================
# DEFINISI KODE WARNA
# ================================================================
WHITE = "\033[97m"   # Putih
CYAN = "\033[96m"
RED = "\033[91m"     # Merah terang
PINK = "\033[95m"    # Pink/Magenta
RESET = "\033[0m"

# ================================================================
# FUNGSI UNTUK MENAMPILKAN LOGO
# ================================================================
def tampilkan_logo():
    logo = """\

██████  ██████   ██████  ██████  ██   ██      ██ ██    ██ ███    ██  ██████  ██      ███████ ██████  
██   ██ ██   ██ ██    ██ ██   ██  ██ ██       ██ ██    ██ ████   ██ ██       ██      ██      ██   ██ 
██   ██ ██████  ██    ██ ██████    ███        ██ ██    ██ ██ ██  ██ ██   ███ ██      █████   ██████  
██   ██ ██   ██ ██    ██ ██       ██ ██  ██   ██ ██    ██ ██  ██ ██ ██    ██ ██      ██      ██   ██ 
██████  ██   ██  ██████  ██      ██   ██  █████   ██████  ██   ████  ██████  ███████ ███████ ██   ██ 
                                    
                                         RESHARESHING TOOLS 
                                
"""
    print(logo)

# ================================================================
# KONFIGURASI
# ================================================================
def load_config(file):
    try:
        with open(file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(RED + f"ERROR: File {file} tidak ditemukan!" + RESET)
        exit()

def load_spreadsheet_id():
    filename = 'spreadsheet_id.txt'
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return f.read().strip()  # File harus berisi hanya Spreadsheet ID
    else:
        return input(RED + "File spreadsheet_id.txt tidak ditemukan! Masukkan Spreadsheet ID: " + RESET).strip()

TELEGRAM_BOT_TOKEN = load_config('token.txt')
TELEGRAM_CHAT_ID = load_config('idchat.txt')
TELEGRAM_THREAD_ID = load_config('threads.txt')
SPREADSHEET_ID = load_spreadsheet_id()

# Inisialisasi Telegram Bot
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

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

# ================================================================
# FUNGSI UTAMA (RESHARESHING)
# ================================================================
def handle_reshareshing():
    FOLDER_NAME = 'data_reshareshing'
    FILE_FIELDS = [
        'situs', 'roadmap', 'whitepiper', 'faucet', 'funding',
        'block_explorer', 'informasi_teamnya', 'twitter',
        'telegram', 'discord', 'github', 'dokumentasi', 'backer'
    ]
    MAIN_FIELDS = {
        "nama_proyek": "Masukkan Nama Proyek          : ",
        "snapshot": "Masukkan Snapshot : ",
        "listing_info": "Masukkan Informasi Listing    : "
    }
    
    if not os.path.exists(FOLDER_NAME):
        os.makedirs(FOLDER_NAME)
    
    use_new_data = input(RED + "Apakah anda pakai data baru? (y/n): " + RESET).strip().lower()
    if use_new_data == 'y':
        # Hapus file data lama (hanya untuk file lokal, bukan di sheet)
        for file in os.listdir(FOLDER_NAME):
            file_path = os.path.join(FOLDER_NAME, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print(RED + "Data lama telah dihapus, silakan masukkan data baru.\n" + RESET)
        force_prompt = True
    elif use_new_data == 'n':
        print(RED + "Menggunakan data yang sudah ada (jika tersedia)" + RESET)
        force_prompt = False
    else:
        print(RED + "Input tidak dikenali, menggunakan data yang sudah ada (jika tersedia)" + RESET)
        force_prompt = False
    
    def get_main_field_value(field, prompt, force_prompt):
        file_path = os.path.join(FOLDER_NAME, f"{field}.txt")
        if os.path.exists(file_path):
            if force_prompt:
                new_value = input(RED + prompt + RESET).strip()
                if new_value:
                    with open(file_path, 'w') as f:
                        f.write(new_value)
                    return new_value
                else:
                    with open(file_path, 'r') as f:
                        return f.read().strip()
            else:
                with open(file_path, 'r') as f:
                    return f.read().strip()
        else:
            value = input(RED + prompt + RESET).strip()
            with open(file_path, 'w') as f:
                f.write(value)
            return value
    
    project_name = get_main_field_value("nama_proyek", MAIN_FIELDS["nama_proyek"], force_prompt)
    snapshot_date = get_main_field_value("snapshot", MAIN_FIELDS["snapshot"], force_prompt)
    listing_info = get_main_field_value("listing_info", MAIN_FIELDS["listing_info"], force_prompt)
    
    def get_field_value(field):
        file_path = os.path.join(FOLDER_NAME, f"{field}.txt")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read().strip()
        else:
            value = input(RED + f"Masukkan link {field.replace('_', ' ')}: " + RESET).strip()
            with open(file_path, 'w') as f:
                f.write(value)
            return value
    
    field_values = [get_field_value(field) for field in FILE_FIELDS]
    feedback = input(RED + "\n›› Masukan Feedback Anda (tekan Enter untuk skip): " + RESET).strip()
    
    # Susun data: total 18 elemen
    # (timestamp, nama proyek, 13 field, snapshot, listing info, feedback)
    # Format tanggal diubah menjadi "%H:%M:%S %d/%m/%Y"
    data = [
        datetime.datetime.now().strftime('%H:%M:%S %d/%m/%Y'),
        project_name,
        *field_values,
        snapshot_date,
        listing_info,
        feedback
    ]
    return data, FILE_FIELDS

# ================================================================
# FUNGSI PENGIRIMAN
# ================================================================
async def send_telegram(summary):
    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=summary,
        message_thread_id=int(TELEGRAM_THREAD_ID),
        parse_mode="HTML"
    )

def send_to_sheets(data, sheet_name):
    header = [
        "Timestamp",
        "Nama proyek",
        "Situs",
        "Roadmap",
        "Whitepiper",
        "Faucet",
        "Funding",
        "Block_explorer",
        "Informasi_teamnya",
        "Twitter",
        "Telegram",
        "Discord",
        "Github",
        "Dokumentasi",
        "Backer",
        "Tanggal snapshot",
        "Informasi listing",
        "Feedback"
    ]
    
    # Ambil seluruh isi sheet (hanya baris yang ada isinya)
    result_all = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_name
    ).execute()
    values_all = result_all.get('values', [])
    
    # Jika sheet kosong atau header tidak sesuai, tulis header di A1:R1
    if not values_all or values_all[0] != header:
        header_range = f"{sheet_name}!A1:R1"
        body_header = {'values': [header]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=header_range,
            valueInputOption='USER_ENTERED',
            body=body_header
        ).execute()
        print(RED + "Header berhasil ditulis di A1:R1." + RESET)
        data_count = 0
    else:
        # Hitung jumlah baris data yang tidak kosong (abaikan baris kosong)
        data_rows = [row for row in values_all[1:] if any(cell.strip() for cell in row if isinstance(cell, str))]
        data_count = len(data_rows)
    
    # Baris data baru yang diinginkan adalah 2 * (data_count + 1)
    next_data_row = 2 * (data_count + 1)
    data_range = f"{sheet_name}!A{next_data_row}:R{next_data_row}"
    
    body_data = {'values': [data]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=data_range,
        valueInputOption='USER_ENTERED',
        body=body_data
    ).execute()
    print(RED + f"Data berhasil ditambahkan di {data_range}." + RESET)
    
    # Tambahkan marker "M" di kolom Y pada baris yang sama dengan data
    marker_range = f"{sheet_name}!Y{next_data_row}:Y{next_data_row}"
    body_marker = {'values': [["M"]]}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=marker_range,
        valueInputOption='USER_ENTERED',
        body=body_marker
    ).execute()
    print(RED + f"Marker 'M' berhasil ditambahkan di {marker_range}" + RESET)

def print_boxed(title, lines):
    max_length = max(len(line) for line in lines) if lines else 0
    max_length = max(max_length, len(title), 40)
    separator = '═' * (max_length + 2)
    
    print(RED + f"\n╔{separator}╗")
    print(f"║ {title.center(max_length)} ║")
    print(f"╠{separator}╣")
    for line in lines:
        print(f"║ {line.ljust(max_length)} ║")
    print(f"╚{separator}╝" + RESET)

# ================================================================
# FUNGSI UTAMA
# ================================================================
def main():
    # Tampilkan logo
    tampilkan_logo()
    
    while True:
        data, file_fields = handle_reshareshing()
        
        labels = (
            ["Timestamp", "Nama Proyek"] +
            [field.capitalize().replace('_', ' ') for field in file_fields] +
            ["Tanggal Snapshot", "Informasi Listing", "Feedback"]
        )
        
        preview_lines = [f"{label}: {value}" for label, value in zip(labels, data)]
        print_boxed("PREVIEW DATA RESHARESHING", preview_lines)
        
        confirm = input(RED + "Apakah anda yakin (y/n): " + RESET).strip().lower()
        if confirm == 'y':
            break
        else:
            print(RED + "\nMengulang input data...\n" + RESET)
    
    summary = "📋 <b>Ringkasan Data Reshareshing</b>\n\n" + "\n".join(
        [f"• <b>{label}</b>: {value}" for label, value in zip(labels, data)]
    )
    # Jalankan pengiriman telegram menggunakan event loop yang aktif
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_telegram(summary))
    send_to_sheets(data, "reshareshing")
    print(RED + "\n✅ Data berhasil dikirim!" + RESET)

# ================================================================
# EKSEKUSI UTAMA DENGAN PENANGANAN ERROR
# ================================================================
def main_menu():
    main()

if __name__ == '__main__':
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n{RED}🚫 Program dihentikan paksa!{RESET}")
    except Exception as e:
        print(f"{RED}💥 Error tidak terduga {str(e)}{RESET}")
