import os
import datetime
import asyncio
import telegram
from google.oauth2 import service_account
from googleapiclient.discovery import build
import nest_asyncio

# Terapkan nest_asyncio jika diperlukan (misalnya, di Jupyter)
nest_asyncio.apply()

# ================================================================
# DEFINISI KODE WARNA ANSI
# ================================================================
WHITE = "\033[97m"
CYAN = "\033[96m"
RED = "\033[91m"
PINK = "\033[95m"
RESET = "\033[0m"

# ================================================================
# FUNGSI UTILITAS
# ================================================================
def tampilkan_logo():
    """Menampilkan logo ASCII."""
    logo = """
██████  ██████    ██████  ██████  ██   ██      ██ ██   ██ ███    ██  ██████  ██       ███████ ██████
██   ██ ██   ██ ██    ██ ██   ██  ██ ██        ██ ██   ██ ████   ██ ██       ██       ██      ██   ██
██   ██ ██████  ██    ██ ██████    ███         ██ ██   ██ ██ ██  ██ ██   ███ ██       █████   ██████
██   ██ ██   ██ ██    ██ ██        ██ ██  ██   ██ ██   ██ ██  ██ ██ ██    ██ ██       ██      ██   ██
██████  ██   ██  ██████  ██       ██   ██  █████   ██████  ██   ████  ██████  ███████ ███████ ██   ██

                                RESHARESHING TOOLS
"""
    print(WHITE + logo + RESET)

def load_config(filepath, error_message):
    """Memuat konfigurasi dari file teks."""
    try:
        with open(filepath, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(RED + f"ERROR: {error_message} ({filepath} tidak ditemukan!)" + RESET)
        exit(1) # Keluar jika file konfigurasi penting tidak ada

def print_boxed(title, lines):
    """Mencetak output dalam format kotak."""
    if not lines:
        max_length = len(title)
    else:
        max_length = max(len(line) for line in lines)
    max_length = max(max_length, len(title), 40) # Pastikan lebar minimum
    separator = '═' * (max_length + 2)

    print(CYAN + f"\n╔{separator}╗")
    print(f"║ {title.center(max_length)} ║")
    print(f"╠{separator}╣")
    for line in lines:
        print(f"║ {line.ljust(max_length)} ║")
    print(f"╚{separator}╝" + RESET)

# ================================================================
# KONFIGURASI & INISIALISASI
# ================================================================
# --- Muat Konfigurasi ---
TELEGRAM_BOT_TOKEN = load_config('token.txt', 'File token bot Telegram')
TELEGRAM_CHAT_ID = load_config('idchat.txt', 'File ID chat Telegram')
TELEGRAM_THREAD_ID = load_config('threads.txt', 'File ID thread Telegram')

# --- Muat Spreadsheet ID ---
SPREADSHEET_ID_FILE = 'spreadsheet_id.txt'
if os.path.exists(SPREADSHEET_ID_FILE):
    SPREADSHEET_ID = load_config(SPREADSHEET_ID_FILE, 'File Spreadsheet ID')
else:
    SPREADSHEET_ID = input(RED + f"{SPREADSHEET_ID_FILE} tidak ditemukan. Masukkan Spreadsheet ID: " + RESET).strip()
    if not SPREADSHEET_ID:
        print(RED + "ERROR: Spreadsheet ID tidak boleh kosong!" + RESET)
        exit(1)
    # Simpan ID yang baru dimasukkan untuk penggunaan selanjutnya
    with open(SPREADSHEET_ID_FILE, 'w') as f:
        f.write(SPREADSHEET_ID)
    print(CYAN + f"Spreadsheet ID disimpan ke {SPREADSHEET_ID_FILE}." + RESET)


# --- Inisialisasi Klien API ---
try:
    # Telegram Bot
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

    # Google Sheets API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    # Cari credentials.json di direktori induk (asumsi struktur DROPXJUNGLER/reshareshing)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
    credentials_path = os.path.join(parent_dir, 'credentials.json')

    if not os.path.exists(credentials_path):
         # Coba cari di direktori yang sama jika tidak ada di induk
         credentials_path = os.path.join(script_dir, 'credentials.json')
         if not os.path.exists(credentials_path):
             print(RED + f"ERROR: File credentials.json tidak ditemukan di {parent_dir} atau {script_dir}!" + RESET)
             exit(1)

    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=creds)

except Exception as e:
    print(RED + f"Error saat inisialisasi: {e}" + RESET)
    exit(1)

# --- Konfigurasi Reshareshing ---
FOLDER_NAME = 'data_reshareshing'
FILE_FIELDS = [
    'situs', 'roadmap', 'whitepiper', 'faucet', 'funding',
    'block_explorer', 'informasi_teamnya', 'twitter',
    'telegram', 'discord', 'github', 'dokumentasi', 'backer'
]
MAIN_FIELDS_PROMPTS = {
    "nama_proyek": "Masukkan Nama Proyek        : ",
    "snapshot": "Masukkan Tanggal Snapshot   : ",
    "listing_info": "Masukkan Informasi Listing  : "
}
SHEET_NAME = "reshareshing" # Nama sheet target

# ================================================================
# FUNGSI INPUT DATA RESHARESHING
# ================================================================
def get_data_from_file_or_prompt(field_name, prompt_text, folder, force_prompt):
    """Mendapatkan data dari file cache atau meminta input pengguna."""
    file_path = os.path.join(folder, f"{field_name}.txt")
    value = ""
    file_exists = os.path.exists(file_path)

    if file_exists and not force_prompt:
        with open(file_path, 'r') as f:
            value = f.read().strip()
        print(f"{CYAN}Info:{RESET} Menggunakan data '{field_name}' dari cache.")
        return value
    else:
        # Minta input jika file tidak ada ATAU jika dipaksa (force_prompt)
        value = input(RED + prompt_text + RESET).strip()
        # Jika dipaksa & input kosong, coba gunakan nilai lama jika ada
        if force_prompt and not value and file_exists:
             with open(file_path, 'r') as f:
                old_value = f.read().strip()
             print(f"{CYAN}Info:{RESET} Input kosong, menggunakan nilai lama '{old_value}' untuk '{field_name}'.")
             return old_value # Kembalikan nilai lama, jangan simpan ulang string kosong

        # Simpan nilai baru (atau nilai lama jika input kosong saat force_prompt)
        with open(file_path, 'w') as f:
            f.write(value)
        return value

def handle_reshareshing():
    """Mengumpulkan semua data yang diperlukan untuk reshareshing."""
    if not os.path.exists(FOLDER_NAME):
        os.makedirs(FOLDER_NAME)
        print(f"{CYAN}Info:{RESET} Folder '{FOLDER_NAME}' dibuat.")

    force_prompt = False
    use_new_data = input(RED + "Gunakan data baru (hapus cache lama)? (y/n): " + RESET).strip().lower()
    if use_new_data == 'y':
        try:
            for file in os.listdir(FOLDER_NAME):
                file_path = os.path.join(FOLDER_NAME, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            print(RED + "Cache data lama dihapus. Masukkan data baru." + RESET)
            force_prompt = True
        except OSError as e:
            print(RED + f"Error saat menghapus cache: {e}" + RESET)
    elif use_new_data == 'n':
        print(CYAN + "Info: Menggunakan data cache (jika ada)." + RESET)
    else:
        print(RED + "Input tidak valid. Menggunakan data cache (jika ada)." + RESET)

    print("-" * 30) # Pemisah

    # --- Ambil Data Utama ---
    main_data = {}
    for field, prompt in MAIN_FIELDS_PROMPTS.items():
        main_data[field] = get_data_from_file_or_prompt(field, prompt, FOLDER_NAME, force_prompt)

    # --- Ambil Data Link/Detail ---
    detail_data_values = []
    for field in FILE_FIELDS:
        prompt = f"Masukkan Link {field.replace('_', ' ').capitalize()} : "
        detail_data_values.append(get_data_from_file_or_prompt(field, prompt, FOLDER_NAME, force_prompt))

    # --- Ambil Feedback ---
    feedback = get_data_from_file_or_prompt("feedback", "\nMasukkan Feedback (Enter untuk skip): ", FOLDER_NAME, force_prompt)
    print("-" * 30) # Pemisah

    # --- Susun Data Akhir ---
    timestamp = datetime.datetime.now().strftime('%H:%M:%S %d/%m/%Y')
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
async def send_telegram(summary):
    """Mengirim ringkasan data ke grup/thread Telegram."""
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=summary,
            message_thread_id=int(TELEGRAM_THREAD_ID), # Pastikan integer
            parse_mode="HTML" # Gunakan HTML untuk bold
        )
        print(CYAN + "Info: Ringkasan berhasil dikirim ke Telegram." + RESET)
    except telegram.error.TelegramError as e:
        print(RED + f"Error Telegram: {e}" + RESET)
    except ValueError:
         print(RED + "Error: TELEGRAM_THREAD_ID harus berupa angka." + RESET)
    except Exception as e:
        print(RED + f"Error tak terduga saat mengirim ke Telegram: {e}" + RESET)


def send_to_sheets(data, sheet_name):
    """Mengirim data ke Google Sheets, memastikan header, dan menambahkan marker."""
    header = [
        "Timestamp", "Nama proyek", "Situs", "Roadmap", "Whitepiper", "Faucet",
        "Funding", "Block_explorer", "Informasi_teamnya", "Twitter", "Telegram",
        "Discord", "Github", "Dokumentasi", "Backer", "Tanggal snapshot",
        "Informasi listing", "Feedback"
    ]
    marker_column = "Y" # Kolom untuk marker 'M'

    try:
        # 1. Periksa Header
        header_range = f"{sheet_name}!A1:{chr(ord('A') + len(header) - 1)}1" # e.g., A1:R1
        result_header = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=header_range
        ).execute()
        current_header = result_header.get('values', [[]])[0]

        if current_header != header:
            body_header = {'values': [header]}
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=header_range,
                valueInputOption='USER_ENTERED',
                body=body_header
            ).execute()
            print(RED + "Info: Header ditulis/diperbarui di baris 1." + RESET)

        # 2. Tambahkan Data (Append)
        append_body = {'values': [data]}
        append_result = sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:A", # Cukup tentukan kolom pertama untuk append
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS', # Sisipkan baris baru
            body=append_body
        ).execute()
        print(CYAN + f"Info: Data berhasil ditambahkan ke sheet '{sheet_name}'." + RESET)

        # 3. Tambahkan Marker 'M'
        updated_range_str = append_result.get('updates', {}).get('updatedRange', '')
        # Contoh updated_range_str: 'reshareshing'!A5:R5
        if '!' in updated_range_str and ':' in updated_range_str:
            try:
                # Ekstrak nomor baris dari range yang diperbarui
                range_part = updated_range_str.split('!')[1] # A5:R5
                start_cell = range_part.split(':')[0] # A5
                row_number = ''.join(filter(str.isdigit, start_cell)) # '5'

                if row_number:
                    marker_range = f"{sheet_name}!{marker_column}{row_number}"
                    body_marker = {'values': [["M"]]}
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=marker_range,
                        valueInputOption='USER_ENTERED',
                        body=body_marker
                    ).execute()
                    print(CYAN + f"Info: Marker 'M' ditambahkan di {marker_range}." + RESET)
                else:
                    print(RED + "Warning: Tidak bisa menentukan baris untuk menambahkan marker." + RESET)
            except Exception as e:
                 print(RED + f"Error saat menambahkan marker: {e}" + RESET)
        else:
            print(RED + f"Warning: Format range ({updated_range_str}) tidak dikenali untuk menambahkan marker." + RESET)

    except Exception as e:
        print(RED + f"Error saat mengirim ke Google Sheets: {e}" + RESET)


# ================================================================
# FUNGSI UTAMA (MAIN EXECUTION)
# ================================================================
def main():
    """Fungsi utama untuk menjalankan alur reshareshing."""
    tampilkan_logo()

    while True:
        collected_data = handle_reshareshing()

        # Buat label yang lebih deskriptif untuk preview dan ringkasan
        labels = [
            "Timestamp", "Nama Proyek", "Situs", "Roadmap", "Whitepaper", "Faucet", # Whitepiper -> Whitepaper?
            "Funding", "Block Explorer", "Informasi Team", "Twitter", "Telegram",
            "Discord", "Github", "Dokumentasi", "Backer", "Tanggal Snapshot",
            "Informasi Listing", "Feedback"
        ]

        # Tampilkan preview data yang akan dikirim
        preview_lines = [f"{label}: {value}" for label, value in zip(labels, collected_data)]
        print_boxed("PREVIEW DATA YANG AKAN DIKIRIM", preview_lines)

        # Konfirmasi sebelum mengirim
        confirm = input(RED + "\nKirim data ini? (y/n): " + RESET).strip().lower()
        if confirm == 'y':
            break # Lanjutkan ke pengiriman
        elif confirm == 'n':
            print(RED + "\nInput data dibatalkan. Mengulang..." + RESET)
            # Loop akan berlanjut untuk input ulang
        else:
            print(RED + "\nPilihan tidak valid. Mengulang input data..." + RESET)


    # Buat ringkasan untuk Telegram (dengan format HTML)
    summary_lines = [f"• <b>{label}:</b> {value}" for label, value in zip(labels, collected_data)]
    telegram_summary = "📋 <b>Ringkasan Data Reshareshing</b>\n\n" + "\n".join(summary_lines)

    try:
        # Kirim ke Telegram (asinkron)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_telegram(telegram_summary))

        # Kirim ke Google Sheets (sinkron)
        send_to_sheets(collected_data, SHEET_NAME)

        print(GREEN + "\n✅ Proses Reshareshing Selesai!" + RESET) # Ganti warna sukses

    except Exception as e:
        print(RED + f"\n💥 Terjadi error saat proses pengiriman: {e}" + RESET)


if __name__ == '__main__':
    # Definisikan GREEN agar bisa dipakai di blok sukses
    GREEN = "\033[92m"
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{RED}🚫 Program dihentikan oleh pengguna.{RESET}")
    except Exception as e:
        # Tangkap error tak terduga di level tertinggi
        print(f"{RED}💥 Error fatal tidak terduga: {e}{RESET}")
        import traceback
        traceback.print_exc() # Cetak traceback untuk debugging
    finally:
         print("\nKeluar dari program.")
