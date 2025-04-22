import os
import datetime
import asyncio
import telegram
from google.oauth2 import service_account
from googleapiclient.discovery import build
import nest_asyncio
import traceback # Import traceback untuk debugging error fatal

# Terapkan nest_asyncio jika diperlukan (misalnya, di Jupyter)
# Pastikan ini dipanggil sebelum loop event asyncio dibuat/digunakan
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        print("Info: Asyncio loop is running, applying nest_asyncio.")
        nest_asyncio.apply()
    else:
        # Jika loop tidak berjalan, tidak perlu nest_asyncio
        pass
except RuntimeError:
    # Jika tidak ada event loop saat ini, nest_asyncio mungkin diperlukan nanti
     print("Info: No current asyncio event loop, applying nest_asyncio.")
     nest_asyncio.apply()


# ================================================================
# DEFINISI KODE WARNA ANSI
# ================================================================
WHITE = "\033[97m"
CYAN = "\033[96m"
RED = "\033[91m"
PINK = "\033[95m"
GREEN = "\033[92m" # Tambahkan warna hijau untuk sukses
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
    print(WHITE + logo + RESET)

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

    # Jika file tidak ada, kosong, atau gagal dibaca
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
                 # Tetap lanjutkan dengan ID yang diinput, tapi beri tahu user
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

# --- Muat Semua Konfigurasi ---
print(PINK + "\n--- Memuat Konfigurasi ---" + RESET)
# Muat konfigurasi wajib
for var_name, (filename, description) in CONFIG_FILES.items():
    globals()[var_name] = load_mandatory_config(filename, description)

# Muat Spreadsheet ID (dengan fallback input)
SPREADSHEET_ID_FILE = 'spreadsheet_id.txt'
SPREADSHEET_ID = load_spreadsheet_id(SPREADSHEET_ID_FILE)

# Cari dan validasi file credentials
CREDENTIALS_FILE_PATH = find_credentials_file()
print(PINK + "--- Konfigurasi Selesai Dimuat ---\n" + RESET)

# ================================================================
# INISIALISASI KLIEN API
# ================================================================
print(PINK + "--- Inisialisasi Klien API ---" + RESET)
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
print(PINK + "--- Inisialisasi Klien API Selesai ---\n" + RESET)

# ================================================================
# KONFIGURASI SPESIFIK RESHARESHING
# ================================================================
FOLDER_NAME = 'data_reshareshing'
# Urutan field ini PENTING karena menentukan urutan kolom di preview & sheets
# Sesuaikan label di `main()` jika urutan/nama file diubah
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
SHEET_NAME = "reshareshing" # Nama sheet target di Google Sheets
MARKER_COLUMN = "Y" # Kolom untuk tanda 'M'

# ================================================================
# FUNGSI INPUT DATA RESHARESHING
# ================================================================
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
            # Anggap cache valid jika file ada & tidak dipaksa prompt ulang
            read_from_cache = True
            print(f"{CYAN}Info:{RESET} Menggunakan data '{field_name}' dari cache.")
            return value
        except Exception as e:
            print(RED + f"Warning:{RESET} Gagal membaca cache '{file_path}': {e}. Akan meminta input.")
            # Jika gagal baca cache, anggap saja tidak ada cache
            file_exists = False # Anggap file tidak bisa digunakan

    # Minta input jika:
    # 1. File tidak ada
    # 2. force_prompt = True
    # 3. Gagal membaca cache (file_exists di-set False di atas)
    if not read_from_cache:
        value = input(RED + prompt_text + RESET).strip()

        # Logika penanganan force_prompt + input kosong:
        if force_prompt and not value and file_exists:
            try:
                with open(file_path, 'r') as f:
                    old_value = f.read().strip()
                print(f"{CYAN}Info:{RESET} Input kosong saat diminta ulang, menggunakan nilai cache lama '{old_value}' untuk '{field_name}'.")
                return old_value # Kembalikan nilai lama, jangan simpan string kosong
            except Exception as e:
                 print(RED + f"Warning:{RESET} Gagal membaca nilai cache lama saat input kosong: {e}. Menggunakan input kosong.")
                 # Lanjutkan dengan nilai kosong jika gagal baca cache lama

        # Simpan nilai baru ke file (termasuk string kosong jika itu inputnya,
        # kecuali dalam kasus force_prompt + input kosong + cache terbaca di atas)
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
            # Mungkin tidak bisa melanjutkan jika folder tak bisa dibuat
            exit(1)

    force_prompt = False
    while True: # Loop untuk memastikan input y/n valid
        use_new_data = input(RED + "Gunakan data baru (hapus cache lama)? (y/n): " + RESET).strip().lower()
        if use_new_data == 'y':
            try:
                cache_files_deleted = 0
                for file in os.listdir(FOLDER_NAME):
                    file_path = os.path.join(FOLDER_NAME, file)
                    if os.path.isfile(file_path) and file.endswith(".txt"): # Hanya hapus file .txt
                        os.remove(file_path)
                        cache_files_deleted += 1
                if cache_files_deleted > 0:
                     print(RED + f"Info: {cache_files_deleted} file cache data lama dihapus. Masukkan data baru." + RESET)
                else:
                     print(CYAN + "Info: Tidak ada file cache untuk dihapus." + RESET)
                force_prompt = True
                break # Keluar loop konfirmasi
            except OSError as e:
                print(RED + f"Error saat menghapus cache: {e}" + RESET)
                # Biarkan user mencoba lagi atau melanjutkan tanpa menghapus
            except Exception as e:
                 print(RED + f"Error tak terduga saat menghapus cache: {e}" + RESET)

        elif use_new_data == 'n':
            print(CYAN + "Info: Menggunakan data cache (jika ada)." + RESET)
            break # Keluar loop konfirmasi
        else:
            print(RED + "Input tidak valid. Harap masukkan 'y' atau 'n'." + RESET)
            # Loop akan berlanjut untuk meminta input lagi

    print("-" * 30) # Pemisah

    # --- Ambil Data Utama ---
    main_data = {}
    for field, prompt in MAIN_FIELDS_PROMPTS.items():
        main_data[field] = get_data_from_file_or_prompt(field, prompt, FOLDER_NAME, force_prompt)

    # --- Ambil Data Link/Detail ---
    # Pastikan urutan di sini sesuai dengan FILE_FIELDS
    detail_data_values = []
    for field in FILE_FIELDS:
        # Membuat prompt yang lebih rapi
        prompt_label = field.replace('_', ' ').capitalize()
        prompt = f"Masukkan Link {prompt_label.ljust(17)}: " # ljust untuk alignment
        detail_data_values.append(get_data_from_file_or_prompt(field, prompt, FOLDER_NAME, force_prompt))

    # --- Ambil Feedback ---
    feedback = get_data_from_file_or_prompt("feedback", "\nMasukkan Feedback (Enter untuk skip): ", FOLDER_NAME, force_prompt)
    print("-" * 30) # Pemisah

    # --- Susun Data Akhir Sesuai Urutan Header ---
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') # Format ISO-like lebih baik untuk sorting
    # Urutan harus MATCH dengan `header` di `send_to_sheets`
    final_data = [
        timestamp,                 # Timestamp
        main_data["nama_proyek"],  # Nama proyek
        *detail_data_values,       # Semua link/detail dari FILE_FIELDS
        main_data["snapshot"],     # Tanggal snapshot
        main_data["listing_info"], # Informasi listing
        feedback                   # Feedback
    ]
    return final_data

# ================================================================
# FUNGSI PENGIRIMAN
# ================================================================
async def send_telegram(summary):
    """Mengirim ringkasan data ke grup/thread Telegram."""
    try:
        # Coba konversi thread ID ke integer di sini, lebih aman
        message_thread_id_int = int(TELEGRAM_THREAD_ID) if TELEGRAM_THREAD_ID else None

        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=summary,
            message_thread_id=message_thread_id_int, # Gunakan ID integer atau None
            parse_mode="HTML" # Gunakan HTML untuk bold, dll.
        )
        print(CYAN + "Info: Ringkasan berhasil dikirim ke Telegram." + RESET)
        return True # Sukses
    except telegram.error.TelegramError as e:
        print(RED + f"Error Telegram: {e}" + RESET)
    except ValueError:
        print(RED + f"Error: TELEGRAM_THREAD_ID ('{TELEGRAM_THREAD_ID}') harus berupa angka atau kosong." + RESET)
    except Exception as e:
        print(RED + f"Error tak terduga saat mengirim ke Telegram: {e}" + RESET)
    return False # Gagal

def send_to_sheets(data, sheet_name):
    """Mengirim data ke Google Sheets, memastikan header, dan menambahkan marker."""
    # Header HARUS sesuai dengan urutan `final_data` di `handle_reshareshing`
    header = [
        "Timestamp", "Nama proyek",
        # Header dari FILE_FIELDS (cocokkan dengan label di `main`)
        "Situs", "Roadmap", "Whitepaper", "Faucet", "Funding", "Block Explorer",
        "Informasi Team", "Twitter", "Telegram", "Discord", "Github",
        "Dokumentasi", "Backer",
        # Header dari MAIN_FIELDS (setelah detail) & Feedback
        "Tanggal snapshot", "Informasi listing", "Feedback",
        # Kolom Tambahan (jika perlu, sesuaikan MARKER_COLUMN jika header berubah)
        # Misal: "Status"
    ]
    # Pastikan MARKER_COLUMN di luar jangkauan header utama jika header berubah
    # Contoh: Jika header sampai kolom R (18), marker bisa di S (19) dst.
    # Kolom ke-18 adalah 'Feedback' (A=1, R=18). Marker di Y (25). OK.
    # Jika header berubah, update MARKER_COLUMN = "S" (atau sesuai kebutuhan)

    try:
        # 1. Dapatkan Metadata Sheet untuk memeriksa keberadaan sheet
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', '')
        sheet_exists = any(s['properties']['title'] == sheet_name for s in sheets)

        if not sheet_exists:
            print(RED + f"Warning: Sheet '{sheet_name}' tidak ditemukan. Mencoba membuatnya..." + RESET)
            requests = [{'addSheet': {'properties': {'title': sheet_name}}}]
            body = {'requests': requests}
            sheets_service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
            print(CYAN + f"Info: Sheet '{sheet_name}' berhasil dibuat." + RESET)
            # Setelah dibuat, header pasti belum ada

        # 2. Periksa/Tulis Header (setelah memastikan sheet ada)
        header_range_end_col = chr(ord('A') + len(header) - 1) # Misal: A s/d R
        header_range = f"{sheet_name}!A1:{header_range_end_col}1"

        result_header = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=header_range
        ).execute()
        current_header = result_header.get('values', [[]])[0]

        # Hanya tulis header jika header kosong atau berbeda
        if not current_header or current_header != header:
            body_header = {'values': [header]}
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=header_range,
                valueInputOption='USER_ENTERED',
                body=body_header
            ).execute()
            print(RED + "Info: Header ditulis/diperbarui di baris 1." + RESET)

        # 3. Tambahkan Data (Append)
        # Pastikan `data` adalah list tunggal di dalam list `values`
        append_body = {'values': [data]}
        append_result = sheets_service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:A", # Cukup kolom A untuk append
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS', # Sisipkan baris baru di akhir data
            body=append_body
        ).execute()
        print(CYAN + f"Info: Data berhasil ditambahkan ke sheet '{sheet_name}'." + RESET)

        # 4. Tambahkan Marker 'M'
        updated_range_str = append_result.get('updates', {}).get('updatedRange', '')
        # Contoh updated_range_str: 'reshareshing'!A5:R5 (jika data sampai R)
        if '!' in updated_range_str and ':' in updated_range_str:
            try:
                range_part = updated_range_str.split('!')[1] # A5:R5
                start_cell = range_part.split(':')[0] # A5
                # Ekstrak nomor baris dengan lebih aman
                row_number_str = ''.join(filter(str.isdigit, start_cell))

                if row_number_str:
                    row_number = int(row_number_str) # Konversi ke integer
                    marker_range = f"{sheet_name}!{MARKER_COLUMN}{row_number}"
                    body_marker = {'values': [["M"]]} # Nilai marker
                    sheets_service.spreadsheets().values().update(
                        spreadsheetId=SPREADSHEET_ID,
                        range=marker_range,
                        valueInputOption='USER_ENTERED',
                        body=body_marker
                    ).execute()
                    print(CYAN + f"Info: Marker 'M' ditambahkan di {marker_range}." + RESET)
                    return True # Sukses
                else:
                    print(RED + "Warning: Tidak bisa menentukan nomor baris dari range ({updated_range_str}) untuk menambahkan marker." + RESET)
            except ValueError:
                 print(RED + f"Warning: Gagal mengurai nomor baris dari '{start_cell}'." + RESET)
            except Exception as e:
                print(RED + f"Error saat menambahkan marker: {e}" + RESET)
        else:
            print(RED + f"Warning: Format range ({updated_range_str}) tidak dikenali untuk menambahkan marker." + RESET)

    except Exception as e:
        print(RED + f"Error saat berinteraksi dengan Google Sheets: {e}" + RESET)
        # Cetak traceback jika error tidak terduga untuk debugging
        if not isinstance(e, (FileNotFoundError, ValueError)): # Jangan print traceback untuk error yg sudah ditangani
             traceback.print_exc()

    return False # Gagal

# ================================================================
# FUNGSI UTAMA (MAIN EXECUTION)
# ================================================================
async def main_async():
    """Fungsi utama asinkron untuk menjalankan alur reshareshing."""
    tampilkan_logo()

    while True: # Loop utama untuk input data
        collected_data = handle_reshareshing()

        # Label untuk preview dan ringkasan (HARUS sesuai urutan `final_data`)
        # Sesuaikan ini jika FILE_FIELDS atau MAIN_FIELDS berubah
        labels = [
            "Timestamp", "Nama Proyek",
            # Label dari FILE_FIELDS
            "Situs", "Roadmap", "Whitepaper", "Faucet", "Funding", "Block Explorer",
            "Informasi Team", "Twitter", "Telegram", "Discord", "Github",
            "Dokumentasi", "Backer",
            # Label dari MAIN_FIELDS & Feedback
            "Tanggal Snapshot", "Informasi Listing", "Feedback"
        ]

        # Pastikan jumlah label sama dengan jumlah data
        if len(labels) != len(collected_data):
             print(RED + f"FATAL ERROR: Jumlah label ({len(labels)}) tidak cocok dengan jumlah data ({len(collected_data)})!" + RESET)
             print(RED + "Periksa urutan/jumlah field di FILE_FIELDS, MAIN_FIELDS_PROMPTS, dan labels di main_async." + RESET)
             exit(1)


        # Tampilkan preview data yang akan dikirim
        preview_lines = [f"{label.ljust(18)}: {value}" for label, value in zip(labels, collected_data)]
        print_boxed("PREVIEW DATA YANG AKAN DIKIRIM", preview_lines)

        # Konfirmasi sebelum mengirim
        while True: # Loop konfirmasi
            confirm = input(RED + "\nKirim data ini? (y/n/q untuk keluar): " + RESET).strip().lower()
            if confirm == 'y':
                break # Lanjutkan ke pengiriman
            elif confirm == 'n':
                print(RED + "\nInput data dibatalkan. Mengulang..." + RESET)
                # Kembali ke awal loop `while True` utama untuk input ulang
                break # Keluar loop konfirmasi, kembali ke loop input utama
            elif confirm == 'q':
                print(RED + "\nProses dibatalkan oleh pengguna." + RESET)
                return # Keluar dari fungsi main_async
            else:
                print(RED + "Pilihan tidak valid. Masukkan 'y', 'n', atau 'q'." + RESET)

        if confirm == 'y':
            # Buat ringkasan untuk Telegram (dengan format HTML)
            summary_lines = []
            for label, value in zip(labels, collected_data):
                 # Handle nilai kosong agar tidak tampil aneh
                 display_value = value if value else "<i>(Kosong)</i>"
                 summary_lines.append(f"• <b>{label}:</b> {display_value}")

            telegram_summary = f"📋 <b>Ringkasan Data Reshareshing - {collected_data[1]}</b>\n\n" + "\n".join(summary_lines) # Index 1 = Nama Proyek

            print("\n--- Memulai Proses Pengiriman ---")
            # Kirim ke Telegram (asinkron)
            telegram_success = await send_telegram(telegram_summary)

            # Kirim ke Google Sheets (sinkron, tapi panggil dari async context)
            # Menjalankannya dalam executor agar tidak memblokir loop event (best practice)
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

            # Tanya apakah ingin input data lagi
            while True:
                 lanjut = input(PINK + "\nInput data lagi? (y/n): " + RESET).strip().lower()
                 if lanjut == 'y':
                     print("\n" + "="*40 + "\n") # Pemisah untuk input baru
                     break # Kembali ke awal loop `while True` utama
                 elif lanjut == 'n':
                     return # Keluar dari fungsi main_async
                 else:
                     print(RED + "Input tidak valid. Masukkan 'y' atau 'n'." + RESET)
            # Jika lanjut == 'y', loop utama akan berlanjut

        elif confirm == 'n':
             # Jika konfirmasi 'n', loop utama akan otomatis mengulang
             continue


# ================================================================
# ENTRY POINT (Jalankan Skrip)
# ================================================================
if __name__ == '__main__':
    try:
        # Gunakan asyncio.run() untuk menjalankan fungsi async utama
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print(f"\n{RED}🚫 Program dihentikan oleh pengguna (Ctrl+C).{RESET}")
    except Exception as e:
        # Tangkap error tak terduga di level tertinggi
        print(f"\n{RED}💥 Error fatal tidak terduga di luar loop utama: {e}{RESET}")
        traceback.print_exc() # Cetak traceback untuk debugging
    finally:
        print(WHITE + "\nKeluar dari program Reshareshing Tools." + RESET)
