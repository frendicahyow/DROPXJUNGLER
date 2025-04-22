import os
import datetime
import asyncio
import telegram
from google.oauth2 import service_account
from googleapiclient.discovery import build
import nest_asyncio
import traceback # Import traceback untuk debugging error fatal

# Pastikan ini dipanggil sebelum loop event asyncio dibuat/digunakan
try:
    loop = asyncio.get_event_loop() # Baris ini mungkin menyebabkan DeprecationWarning jika dipanggil sebelum asyncio.run()
    if loop.is_running():
        print("Info: Asyncio loop is running, applying nest_asyncio.")
        nest_asyncio.apply()
    # Tidak perlu else, jika tidak running, asyncio.run() akan membuat yang baru
except RuntimeError:
     print("Info: No current asyncio event loop, applying nest_asyncio.")
     nest_asyncio.apply()


# ================================================================
# DEFINISI KODE WARNA ANSI
# ================================================================
WHITE = "\033[97m"
CYAN = "\033[96m"
RED = "\033[91m"
PINK = "\033[95m"
GREEN = "\033[92m"
RESET = "\033[0m"

# ================================================================
# FUNGSI UTILITAS
# ================================================================
def tampilkan_logo():
    """Menampilkan logo ASCII."""
    logo = """
████████████ █████████████   ██   ███    ████    ██████████    ████████████     
██   ███   ███    ███   ███ ██    ███    █████   ███     ██    ██    ██   ██    
██   █████████    ███████ ███     ███    ███ ██  ███   ████    █████ ██████     
██   ███   ███    ███    ██ ███   ███    ███  ██ ███    ███    ██    ██   ██    
████████   ██████████   ██   ██████ ████████   ████████████████████████   ██    
    
                          RESHARESHING TOOLS
                   
"""
    print(WHITE + logo + RESET) # Logo dicetak di sini

def print_boxed(title, lines):
    """Mencetak output dalam format kotak."""
    if not lines:
        max_length = len(title)
    else:
        max_length = max(len(line) for line in lines)
    # Pastikan lebar minimum dan akomodasi untuk title
    max_length = max(max_length, len(title), 40)
    separator = '═' * (max_length + 2)

    print(CYAN + f"\n╔{separator}╗")
    print(f"║ {title.center(max_length)} ║")
    print(f"╠{separator}╣")
    if not lines:
        print(f"║ {' '.ljust(max_length)} ║") # Baris kosong jika tidak ada lines
    else:
        for line in lines:
            print(f"║ {line.ljust(max_length)} ║")
    print(f"╚{separator}╝" + RESET)


# ================================================================
# PEMUATAN KONFIGURASI (Refactored)
# ================================================================

def load_mandatory_config(filepath, description):
    """Memuat konfigurasi wajib dari file teks. Keluar jika gagal."""
    try:
        with open(filepath, 'r') as f:
            value = f.read().strip()
            if not value:
                print(RED + f"ERROR: File konfigurasi '{filepath}' ({description}) kosong!" + RESET)
                exit(1)
            # Pesan info dimuat sekarang dicetak SETELAH logo
            print(f"{CYAN}Info:{RESET} Konfigurasi '{description}' dimuat dari '{filepath}'.")
            return value
    except FileNotFoundError:
        print(RED + f"ERROR: File konfigurasi '{filepath}' ({description}) tidak ditemukan!" + RESET)
        exit(1)
    except Exception as e:
        print(RED + f"ERROR: Gagal memuat konfigurasi '{description}' dari '{filepath}': {e}" + RESET)
        exit(1)

def load_spreadsheet_id(filepath):
    """Memuat Spreadsheet ID, meminta input jika file tidak ada."""
    if os.path.exists(filepath):
        spreadsheet_id = ""
        try:
            with open(filepath, 'r') as f:
                spreadsheet_id = f.read().strip()
            if spreadsheet_id:
                print(f"{CYAN}Info:{RESET} Spreadsheet ID dimuat dari '{filepath}'.")
                return spreadsheet_id
            else:
                print(RED + f"Warning:{RESET} File '{filepath}' ada tapi kosong.")
        except Exception as e:
             print(RED + f"Warning:{RESET} Gagal membaca '{filepath}': {e}. Akan meminta input.")

    while True:
        spreadsheet_id = input(RED + f"Masukkan Google Spreadsheet ID: " + RESET).strip()
        if spreadsheet_id:
            try:
                with open(filepath, 'w') as f:
                    f.write(spreadsheet_id)
                print(CYAN + f"Info: Spreadsheet ID disimpan ke '{filepath}'." + RESET)
                return spreadsheet_id
            except Exception as e:
                 print(RED + f"ERROR: Gagal menyimpan Spreadsheet ID ke '{filepath}': {e}" + RESET)
                 return spreadsheet_id
        else:
            print(RED + "ERROR: Spreadsheet ID tidak boleh kosong!" + RESET)


def find_credentials_file():
    """Mencari file credentials.json di direktori saat ini atau induk."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    current_dir_path = os.path.join(script_dir, 'credentials.json')
    parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
    parent_dir_path = os.path.join(parent_dir, 'credentials.json')

    if os.path.exists(parent_dir_path):
        print(f"{CYAN}Info:{RESET} File credentials.json ditemukan di direktori induk: '{parent_dir_path}'")
        return parent_dir_path
    elif os.path.exists(current_dir_path):
         print(f"{CYAN}Info:{RESET} File credentials.json ditemukan di direktori skrip: '{current_dir_path}'")
         return current_dir_path
    else:
        print(RED + f"ERROR: File credentials.json tidak ditemukan di '{parent_dir}' atau '{script_dir}'!" + RESET)
        exit(1)

# --- Daftar Konfigurasi Wajib ---
CONFIG_FILES = {
    'TELEGRAM_BOT_TOKEN': ('token.txt', 'Token Bot Telegram'),
    'TELEGRAM_CHAT_ID': ('idchat.txt', 'ID Chat Telegram'),
    'TELEGRAM_THREAD_ID': ('threads.txt', 'ID Thread Telegram')
}

# --- Muat Semua Konfigurasi (akan dicetak setelah logo) ---
# print(PINK + "\n--- Memuat Konfigurasi ---" + RESET) # Judul bisa dihilangkan jika mau lebih bersih
# Muat konfigurasi wajib
for var_name, (filename, description) in CONFIG_FILES.items():
    globals()[var_name] = load_mandatory_config(filename, description)

# Muat Spreadsheet ID (dengan fallback input)
SPREADSHEET_ID_FILE = 'spreadsheet_id.txt'
SPREADSHEET_ID = load_spreadsheet_id(SPREADSHEET_ID_FILE)

# Cari dan validasi file credentials
CREDENTIALS_FILE_PATH = find_credentials_file()
# print(PINK + "--- Konfigurasi Selesai Dimuat ---\n" + RESET) # Judul bisa dihilangkan

# ================================================================
# INISIALISASI KLIEN API (akan dicetak setelah logo & config)
# ================================================================
# print(PINK + "--- Inisialisasi Klien API ---" + RESET) # Judul bisa dihilangkan
try:
    # Telegram Bot
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    print(f"{CYAN}Info:{RESET} Klien Telegram Bot berhasil diinisialisasi.")

    # Google Sheets API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE_PATH, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=creds)
    print(f"{CYAN}Info:{RESET} Klien Google Sheets API berhasil diinisialisasi.")

except Exception as e:
    print(RED + f"ERROR saat inisialisasi klien API: {e}" + RESET)
    exit(1)
# print(PINK + "--- Inisialisasi Klien API Selesai ---\n" + RESET) # Judul bisa dihilangkan


# ================================================================
# KONFIGURASI SPESIFIK RESHARESHING
# ================================================================
FOLDER_NAME = 'data_reshareshing'
FILE_FIELDS = [
    'situs', 'roadmap', 'whitepiper', 'faucet', 'funding',
    'block_explorer', 'informasi_teamnya', 'twitter',
    'telegram', 'discord', 'github', 'dokumentasi', 'backer'
]
MAIN_FIELDS_PROMPTS = {
    "nama_proyek": "Masukkan Nama Proyek         : ",
    "snapshot": "Masukkan Tanggal Snapshot    : ",
    "listing_info": "Masukkan Informasi Listing   : "
}
SHEET_NAME = "reshareshing"
MARKER_COLUMN = "Y"

# ================================================================
# FUNGSI INPUT DATA RESHARESHING
# ================================================================
# ... (Fungsi get_data_from_file_or_prompt dan handle_reshareshing tetap sama) ...
def get_data_from_file_or_prompt(field_name, prompt_text, folder, force_prompt):
    """Mendapatkan data dari file cache atau meminta input pengguna."""
    file_path = os.path.join(folder, f"{field_name}.txt")
    value = ""
    file_exists = os.path.exists(file_path)
    read_from_cache = False

    if file_exists and not force_prompt:
        try:
            with open(file_path, 'r') as f:
                value = f.read().strip()
            read_from_cache = True
            print(f"{CYAN}Info:{RESET} Menggunakan data '{field_name}' dari cache.")
            return value
        except Exception as e:
            print(RED + f"Warning:{RESET} Gagal membaca cache '{file_path}': {e}. Akan meminta input.")
            file_exists = False

    if not read_from_cache:
        value = input(RED + prompt_text + RESET).strip()
        if force_prompt and not value and file_exists:
            try:
                with open(file_path, 'r') as f:
                    old_value = f.read().strip()
                print(f"{CYAN}Info:{RESET} Input kosong saat diminta ulang, menggunakan nilai cache lama '{old_value}' untuk '{field_name}'.")
                return old_value
            except Exception as e:
                 print(RED + f"Warning:{RESET} Gagal membaca nilai cache lama saat input kosong: {e}. Menggunakan input kosong.")

        try:
            with open(file_path, 'w') as f:
                f.write(value)
        except Exception as e:
            print(RED + f"Warning:{RESET} Gagal menyimpan nilai '{field_name}' ke cache '{file_path}': {e}")
        return value

def handle_reshareshing():
    """Mengumpulkan semua data yang diperlukan untuk reshareshing."""
    if not os.path.exists(FOLDER_NAME):
        try:
            os.makedirs(FOLDER_NAME)
            print(f"{CYAN}Info:{RESET} Folder '{FOLDER_NAME}' dibuat.")
        except OSError as e:
            print(RED + f"ERROR: Gagal membuat folder '{FOLDER_NAME}': {e}" + RESET)
            exit(1)

    force_prompt = False
    while True:
        # Pertanyaan ini akan muncul SETELAH logo dan pesan config/init
        use_new_data = input(RED + "Gunakan data baru (hapus cache lama)? (y/n): " + RESET).strip().lower()
        if use_new_data == 'y':
            try:
                cache_files_deleted = 0
                for file in os.listdir(FOLDER_NAME):
                    file_path = os.path.join(FOLDER_NAME, file)
                    if os.path.isfile(file_path) and file.endswith(".txt"):
                        os.remove(file_path)
                        cache_files_deleted += 1
                if cache_files_deleted > 0:
                     print(RED + f"Info: {cache_files_deleted} file cache data lama dihapus. Masukkan data baru." + RESET)
                else:
                     print(CYAN + "Info: Tidak ada file cache untuk dihapus." + RESET)
                force_prompt = True
                break
            except OSError as e:
                print(RED + f"Error saat menghapus cache: {e}" + RESET)
            except Exception as e:
                 print(RED + f"Error tak terduga saat menghapus cache: {e}" + RESET)
        elif use_new_data == 'n':
            print(CYAN + "Info: Menggunakan data cache (jika ada)." + RESET)
            break
        else:
            print(RED + "Input tidak valid. Harap masukkan 'y' atau 'n'." + RESET)

    print("-" * 30)

    main_data = {}
    for field, prompt in MAIN_FIELDS_PROMPTS.items():
        main_data[field] = get_data_from_file_or_prompt(field, prompt, FOLDER_NAME, force_prompt)

    detail_data_values = []
    for field in FILE_FIELDS:
        prompt_label = field.replace('_', ' ').capitalize()
        prompt = f"Masukkan Link {prompt_label.ljust(17)}: "
        detail_data_values.append(get_data_from_file_or_prompt(field, prompt, FOLDER_NAME, force_prompt))

    feedback = get_data_from_file_or_prompt("feedback", "\nMasukkan Feedback (Enter untuk skip): ", FOLDER_NAME, force_prompt)
    print("-" * 30)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_data = [
        timestamp,
        main_data["nama_proyek"],
        *detail_data_values,
        main_data["snapshot"],
        main_data["listing_info"],
        feedback
    ]
    return final_data

# ================================================================
# FUNGSI PENGIRIMAN
# ================================================================
# ... (Fungsi send_telegram dan send_to_sheets tetap sama) ...
async def send_telegram(summary):
    """Mengirim ringkasan data ke grup/thread Telegram."""
    try:
        message_thread_id_int = int(TELEGRAM_THREAD_ID) if TELEGRAM_THREAD_ID else None
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=summary,
            message_thread_id=message_thread_id_int,
            parse_mode="HTML"
        )
        print(CYAN + "Info: Ringkasan berhasil dikirim ke Telegram." + RESET)
        return True
    except telegram.error.TelegramError as e:
        print(RED + f"Error Telegram: {e}" + RESET)
    except ValueError:
        print(RED + f"Error: TELEGRAM_THREAD_ID ('{TELEGRAM_THREAD_ID}') harus berupa angka atau kosong." + RESET)
    except Exception as e:
        print(RED + f"Error tak terduga saat mengirim ke Telegram: {e}" + RESET)
    return False

def send_to_sheets(data, sheet_name):
    """Mengirim data ke Google Sheets, memastikan header, dan menambahkan marker."""
    header = [
        "Timestamp", "Nama proyek",
        "Situs", "Roadmap", "Whitepaper", "Faucet", "Funding", "Block Explorer",
        "Informasi Team", "Twitter", "Telegram", "Discord", "Github",
        "Dokumentasi", "Backer",
        "Tanggal snapshot", "Informasi listing", "Feedback"
    ]
    try:
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', '')
        sheet_exists = any(s['properties']['title'] == sheet_name for s in sheets)

        if not sheet_exists:
            print(RED + f"Warning: Sheet '{sheet_name}' tidak ditemukan. Mencoba membuatnya..." + RESET)
            requests = [{'addSheet': {'properties': {'title': sheet_name}}}]
            body = {'requests': requests}
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
            print(CYAN + f"Info: Sheet '{sheet_name}' berhasil dibuat." + RESET)

        header_range_end_col = chr(ord('A') + len(header) - 1)
        header_range = f"{sheet_name}!A1:{header_range_end_col}1"

        result_header = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=header_range
        ).execute()
        current_header = result_header.get('values', [[]])[0]

        if not current_header or current_header != header:
            body_header = {'values': [header]}
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=header_range,
                valueInputOption='USER_ENTERED',
                body=body_header
            ).execute()
            print(RED + "Info: Header ditulis/diperbarui di baris 1." + RESET)

        append_body = {'values': [data]}
        append_result = sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:A",
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=append_body
        ).execute()
        print(CYAN + f"Info: Data berhasil ditambahkan ke sheet '{sheet_name}'." + RESET)

        updated_range_str = append_result.get('updates', {}).get('updatedRange', '')
        if '!' in updated_range_str and ':' in updated_range_str:
            try:
                range_part = updated_range_str.split('!')[1]
                start_cell = range_part.split(':')[0]
                row_number_str = ''.join(filter(str.isdigit, start_cell))
                if row_number_str:
                    row_number = int(row_number_str)
                    marker_range = f"{sheet_name}!{MARKER_COLUMN}{row_number}"
                    body_marker = {'values': [["M"]]}
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=marker_range,
                        valueInputOption='USER_ENTERED',
                        body=body_marker
                    ).execute()
                    print(CYAN + f"Info: Marker 'M' ditambahkan di {marker_range}." + RESET)
                    return True
                else:
                    print(RED + f"Warning: Tidak bisa menentukan nomor baris dari range ({updated_range_str}) untuk menambahkan marker." + RESET)
            except ValueError:
                 print(RED + f"Warning: Gagal mengurai nomor baris dari '{start_cell}'." + RESET)
            except Exception as e:
                print(RED + f"Error saat menambahkan marker: {e}" + RESET)
        else:
            print(RED + f"Warning: Format range ({updated_range_str}) tidak dikenali untuk menambahkan marker." + RESET)

    except Exception as e:
        print(RED + f"Error saat berinteraksi dengan Google Sheets: {e}" + RESET)
        if not isinstance(e, (FileNotFoundError, ValueError)):
             traceback.print_exc()
    return False

# ================================================================
# FUNGSI UTAMA (MAIN EXECUTION)
# ================================================================
async def main_async():
    """Fungsi utama asinkron untuk menjalankan alur reshareshing."""
    # tampilkan_logo() # <-- DIHAPUS DARI SINI

    while True: # Loop utama untuk input data
        collected_data = handle_reshareshing()

        labels = [
            "Timestamp", "Nama Proyek",
            "Situs", "Roadmap", "Whitepaper", "Faucet", "Funding", "Block Explorer",
            "Informasi Team", "Twitter", "Telegram", "Discord", "Github",
            "Dokumentasi", "Backer",
            "Tanggal Snapshot", "Informasi Listing", "Feedback"
        ]

        if len(labels) != len(collected_data):
             print(RED + f"FATAL ERROR: Jumlah label ({len(labels)}) tidak cocok dengan jumlah data ({len(collected_data)})!" + RESET)
             print(RED + "Periksa urutan/jumlah field di FILE_FIELDS, MAIN_FIELDS_PROMPTS, dan labels di main_async." + RESET)
             exit(1)

        preview_lines = [f"{label.ljust(18)}: {value}" for label, value in zip(labels, collected_data)]
        print_boxed("PREVIEW DATA YANG AKAN DIKIRIM", preview_lines)

        while True:
            confirm = input(RED + "\nKirim data ini? (y/n/q untuk keluar): " + RESET).strip().lower()
            if confirm == 'y':
                break
            elif confirm == 'n':
                print(RED + "\nInput data dibatalkan. Mengulang..." + RESET)
                break
            elif confirm == 'q':
                print(RED + "\nProses dibatalkan oleh pengguna." + RESET)
                return
            else:
                print(RED + "Pilihan tidak valid. Masukkan 'y', 'n', atau 'q'." + RESET)

        if confirm == 'y':
            summary_lines = []
            for label, value in zip(labels, collected_data):
                 display_value = value if value else "<i>(Kosong)</i>"
                 summary_lines.append(f"• <b>{label}:</b> {display_value}")
            telegram_summary = f"📋 <b>Ringkasan Data Reshareshing - {collected_data[1]}</b>\n\n" + "\n".join(summary_lines)

            print("\n--- Memulai Proses Pengiriman ---")
            telegram_success = await send_telegram(telegram_summary)
            loop = asyncio.get_event_loop()
            sheets_success = await loop.run_in_executor(None, send_to_sheets, collected_data, SHEET_NAME)
            print("--- Proses Pengiriman Selesai ---")

            if telegram_success and sheets_success:
                print(GREEN + "\n✅ Data berhasil dikirim ke Telegram dan Google Sheets!" + RESET)
            else:
                print(RED + "\n⚠️ Terjadi masalah saat pengiriman:" + RESET)
                if not telegram_success:
                    print(RED + "   - Gagal mengirim ke Telegram." + RESET)
                if not sheets_success:
                     print(RED + "   - Gagal mengirim ke Google Sheets." + RESET)

            while True:
                 lanjut = input(PINK + "\nInput data lagi? (y/n): " + RESET).strip().lower()
                 if lanjut == 'y':
                     print("\n" + "="*40 + "\n")
                     break
                 elif lanjut == 'n':
                     return
                 else:
                     print(RED + "Input tidak valid. Masukkan 'y' atau 'n'." + RESET)
        elif confirm == 'n':
             continue


# ================================================================
# ENTRY POINT (Jalankan Skrip)
# ================================================================
if __name__ == '__main__':
    # Tampilkan logo SEBELUM memuat konfigurasi atau inisialisasi apapun
    tampilkan_logo() # <-- DIPINDAHKAN KE SINI

    # Beri jeda sedikit agar logo terlihat sebelum pesan lain muncul (opsional)
    # import time
    # time.sleep(0.1)

    print(PINK + "\n--- Memuat Konfigurasi & Inisialisasi ---" + RESET) # Judul gabungan

    try:
        # Jalankan loop async utama SETELAH semua setup selesai
        asyncio.run(main_async())

    except KeyboardInterrupt:
        print(f"\n{RED}🚫 Program dihentikan oleh pengguna (Ctrl+C).{RESET}")
    except Exception as e:
        print(f"\n{RED}💥 Error fatal tidak terduga: {e}{RESET}")
        traceback.print_exc()
    finally:
        print(WHITE + "\nKeluar dari program Reshareshing Tools." + RESET)
