# -- coding: utf-8 --
import re
import datetime
import os
import asyncio
from googleapiclient.discovery import build
from google.oauth2 import service_account
from telegram import Bot
from googleapiclient.errors import HttpError

# Warna output terminal
WHITE = "\033[97m"
PURPLE = "\033[95m"
RESET = "\033[0m"

########################################
# LOGO
########################################
# (Logo tetap sama)
logo = r"""
██████  ██████   ██████  ██████  ██   ██      ██ ██    ██ ███    ██  ██████  ██      ███████ ██████
██   ██ ██   ██ ██    ██ ██   ██  ██ ██       ██ ██    ██ ████   ██ ██       ██      ██      ██   ██
██   ██ ██████  ██    ██ ██████    ███        ██ ██    ██ ██ ██  ██ ██   ███ ██      █████   ██████
██   ██ ██   ██ ██    ██ ██       ██ ██  ██   ██ ██    ██ ██  ██ ██ ██    ██ ██      ██      ██   ██
██████  ██   ██  ██████  ██      ██   ██  █████   ██████  ██   ████  ██████  ███████ ███████ ██   ██

                                         MONITORING  TOOLS
"""
print(WHITE + logo + RESET)

########################################
# UTILITAS
########################################
# (read_file, parse_spreadsheet_ids tetap sama)
def read_file(filename):
    """Baca file dan kembalikan isinya (strip spasi)."""
    try:
        with open(filename, "r", encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        if filename not in ["Threads.txt"]:
             print(f"{PURPLE}❌ File {filename} tidak ditemukan.{RESET}")
        return None
    except Exception as e:
        print(f"{PURPLE}❌ Gagal membaca {filename}: {e}{RESET}")
        return None

def parse_spreadsheet_ids(filename):
    """Parse spreadsheet IDs dari file."""
    content = read_file(filename)
    ids = {}
    if content:
        try:
            for line in content.splitlines():
                line = line.strip()
                if ":" in line and not line.startswith('#'):
                    key, val = line.split(":", 1)
                    ids[key.strip()] = val.strip()
        except Exception as e:
             print(f"{PURPLE}❌ Gagal memproses {filename}. Format 'Nama: ID'. Error: {e}{RESET}")
    return ids

########################################
# KONFIGURASI
########################################
# (daily_categories, weekly_categories, monthly_categories tetap sama)
daily_categories   = [
    "Reshareshing", "Analysis", "Strategy", "Moderator",
    "Dimas", "Agung", "Anang", "Tayong", "Agus", "Frendi", "Ulan",
    "Solihin", "Agus japan", "Reza"
]
# --- Kategori yang menjadi patokan utama untuk performa harian ---
BENCHMARK_CATEGORIES = ["Reshareshing", "Analysis", "Strategy"]

weekly_categories  = ["listairdrop"]
monthly_categories = ["Datacurator"]

spreadsheet_ids = parse_spreadsheet_ids("mospreadsheet_id.txt")

if "listairdrop" not in spreadsheet_ids and "Moderator" in spreadsheet_ids:
    print(f"{PURPLE}ℹ Menggunakan Spreadsheet ID 'Moderator' untuk 'listairdrop'.{RESET}")
    spreadsheet_ids["listairdrop"] = spreadsheet_ids["Moderator"]
elif "listairdrop" not in spreadsheet_ids and "Moderator" not in spreadsheet_ids:
     print(f"{PURPLE}⚠ Peringatan: Spreadsheet ID untuk 'listairdrop' atau 'Moderator' tidak ditemukan.{RESET}")
elif "listairdrop" not in spreadsheet_ids and "Moderator" in spreadsheet_ids:
     print(f"{PURPLE}⚠ Peringatan: ID 'listairdrop' tidak ada. Menggunakan ID 'Moderator'.{RESET}")
     spreadsheet_ids["listairdrop"] = spreadsheet_ids["Moderator"]

sheet_names = {
    "Reshareshing": "Reshareshing", "Analysis": "Analysis", "Strategy": "Strategy",
    "Moderator": "Moderator", "listairdrop": "listairdrop", "Datacurator": "Datacurator"
}
marker_columns = {"Datacurator": "AY"}

monitoring_header = [
    "Timestamp", "Reshareshing", "Analysis", "Strategy", "Moderator", "ListAirdrop",
    "Dimas", "Agung", "Anang", "Tayong", "Agus", "Frendi", "Ulan",
    "Solihin", "Agus japan", "Reza", "Datacurator"
]

NUM_COLUMNS = len(monitoring_header)
LAST_COLUMN_LETTER = chr(ord('A') + NUM_COLUMNS - 1)

monitoring_id = read_file("monitoringid.txt")
telegram_token = read_file("Token.txt")
telegram_chat_id = read_file("Idchat.txt")
threads_text = read_file("Threads.txt")
thread_ids = None
if threads_text:
    try:
        thread_ids = [int(line.strip()) for line in threads_text.splitlines() if line.strip().isdigit()]
        if not thread_ids:
            print(f"{PURPLE}⚠ Threads.txt ada tapi tidak berisi ID thread numerik.{RESET}")
            thread_ids = None
    except ValueError:
        print(f"{PURPLE}❌ Gagal baca Thread ID. Pastikan hanya angka per baris.{RESET}")
        thread_ids = None

if not monitoring_id: print(f"{PURPLE}❌ FATAL: monitoringid.txt kosong/tidak ada.{RESET}"); exit()
if not telegram_token or not telegram_chat_id: print(f"{PURPLE}⚠ Peringatan: Token/Chat ID Telegram kosong/tidak ada. Notifikasi tidak akan dikirim.{RESET}")

########################################
# GOOGLE SHEETS API
########################################
# (Inisialisasi API tetap sama)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
script_dir = os.path.dirname(os.path.realpath(_file_))
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
credentials_path = os.path.join(parent_dir, 'credentials.json')
creds = None
sheets_service = None
try:
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    sheets_service = build('sheets', 'v4', credentials=creds)
    print(f"{PURPLE}🔑 Kredensial Google berhasil dimuat.{RESET}")
except FileNotFoundError: print(f"{PURPLE}❌ FATAL: credentials.json tidak ditemukan di '{parent_dir}'.{RESET}"); exit()
except Exception as e: print(f"{PURPLE}❌ FATAL: Gagal muat kredensial/build service: {e}.{RESET}"); exit()

########################################
# HEADER & MONITORING FUNCTIONS
########################################
# (ensure_monitoring_header, count_marker, monitor_categories tetap sama)
def ensure_monitoring_header():
    """Pastikan header Monitoring ada di sheet pertama sesuai monitoring_header."""
    if not sheets_service or not monitoring_id: return
    try:
        spreadsheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=monitoring_id).execute()
        first_sheet_name = spreadsheet_metadata['sheets'][0]['properties']['title']
        header_range = f"'{first_sheet_name}'!A1:{LAST_COLUMN_LETTER}1"
        result = sheets_service.spreadsheets().values().get(spreadsheetId=monitoring_id, range=header_range, majorDimension="ROWS").execute()
        values = result.get("values", [])
        if values and values[0] == monitoring_header:
            # print(f"{PURPLE}👍 Header Monitoring sudah sesuai di '{first_sheet_name}'.{RESET}") # Kurangi pesan
            return
        print(f"{PURPLE}📝 Memperbarui header Monitoring di sheet '{first_sheet_name}'...{RESET}")
        body = {"values": [monitoring_header]}
        sheets_service.spreadsheets().values().update(spreadsheetId=monitoring_id, range=header_range, valueInputOption="USER_ENTERED", body=body).execute()
        print(f"{PURPLE}✅ Header Monitoring (A:{LAST_COLUMN_LETTER}) telah dipastikan di '{first_sheet_name}'.{RESET}")
    except HttpError as e: print(f"{PURPLE}❌ Gagal memastikan header: {e}{RESET}")
    except Exception as e: print(f"{PURPLE}❌ Gagal memastikan header (error tak terduga): {e}{RESET}")

def count_marker(sheet_id, sheet_name, marker_col="Y"):
    """Hitung 'M' di kolom marker pada sheet yang ditentukan."""
    if not sheets_service or not sheet_id: return 0
    safe_sheet_name = f"'{sheet_name.replace("'", "''")}'"; range_name = f"{safe_sheet_name}!{marker_col}2:{marker_col}"
    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=sheet_id, range=range_name).execute()
        values = result.get("values", []); count = sum(1 for row in values if row and row[0].strip().upper() == "M")
        return count
    except HttpError as e:
         if e.resp.status == 400 and 'Unable to parse range' in str(e): print(f"{PURPLE}❌ Gagal hitung marker: Sheet/range '{sheet_name}'/'{range_name}' tidak valid di ID '{sheet_id}'.{RESET}")
         elif e.resp.status == 403: print(f"{PURPLE}❌ Gagal hitung marker: Tidak ada izin baca spreadsheet ID '{sheet_id}'.{RESET}")
         else: print(f"{PURPLE}❌ Gagal hitung marker di '{sheet_name}' (ID: {sheet_id}): {e}{RESET}")
         return 0
    except Exception as e: print(f"{PURPLE}❌ Gagal hitung marker di '{sheet_name}' (ID: {sheet_id}, error tak terduga): {e}{RESET}"); return 0

def monitor_categories(categories):
    """Hitung interaksi per kategori."""
    results = {}
    print(f"{PURPLE}🔄 Memulai monitoring untuk: {', '.join(categories)}{RESET}")
    # print(f"{PURPLE}🔔 PENTING: Pastikan 'mospreadsheet_id.txt' update untuk anggota baru.{RESET}") # Pindah ke awal
    for cat in categories:
        sheet_id = spreadsheet_ids.get(cat)
        s_name = sheet_names.get(cat, cat); marker_col = marker_columns.get(cat, "Y")
        if sheet_id: results[cat] = count_marker(sheet_id, s_name, marker_col)
        else: print(f"{PURPLE}⚠ Kategori '{cat}' tidak ada Spreadsheet ID di mospreadsheet_id.txt. Hasil = 0.{RESET}"); results[cat] = 0
    print(f"{PURPLE}📊 Hasil sementara: {results}{RESET}")
    return results

# --- LANGKAH 1: Fungsi Helper Baru ---
def find_low_interaction(results, categories_to_check, benchmark_categories):
    """
    Identifikasi kategori/anggota yang interaksinya di bawah benchmark.

    Args:
        results (dict): Hasil monitoring {nama_kategori: jumlah_interaksi}.
        categories_to_check (list): Daftar nama kategori/anggota yang akan diperiksa.
        benchmark_categories (list): Daftar nama kategori yang menjadi patokan.

    Returns:
        tuple: (list_kurang_interaksi, nilai_benchmark)
               list_kurang_interaksi berisi string "Nama: Jumlah".
               nilai_benchmark adalah integer.
               Mengembalikan ([], 0) jika tidak ada hasil atau benchmark 0.
    """
    if not results:
        return [], 0

    # Tentukan nilai benchmark (maksimum dari kategori patokan)
    benchmark_values = [results.get(cat, 0) for cat in benchmark_categories]
    benchmark_value = max(benchmark_values) if benchmark_values else 0

    print(f"{PURPLE}🎯 Benchmark hari ini (Max dari {', '.join(benchmark_categories)}): {benchmark_value}{RESET}")

    # Jika benchmark 0, tidak ada yang bisa di bawahnya
    if benchmark_value == 0:
        print(f"{PURPLE}ℹ Benchmark 0, tidak ada pengecekan performa.{RESET}")
        return [], 0

    low_interaction_list = []
    for cat in categories_to_check:
        count = results.get(cat, 0)
        if count < benchmark_value:
            low_interaction_list.append(f"{cat}: {count}")
            print(f"{PURPLE}📉 Terdeteksi kurang interaksi: {cat} ({count}) < {benchmark_value}{RESET}")

    return low_interaction_list, benchmark_value

########################################
# TOTAL CALCULATION & DATA CLEANUP
########################################
# (calculate_total_monitoring, delete_data_rows, delete_sheet_by_name tetap sama)
def calculate_total_monitoring():
    """Hitung total dari semua data mentah di sheet pertama."""
    if not sheets_service or not monitoring_id: return {}, 0
    try:
        spreadsheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=monitoring_id).execute()
        if not spreadsheet_metadata.get('sheets'): print(f"{PURPLE}❌ Gagal hitung total: Tidak ada sheet di ID '{monitoring_id}'.{RESET}"); return {}, 0
        first_sheet_name = spreadsheet_metadata['sheets'][0]['properties']['title']; range_name = f"'{first_sheet_name}'!A2:{LAST_COLUMN_LETTER}"
        print(f"{PURPLE}📊 Menghitung total dari '{first_sheet_name}' range {range_name}...{RESET}")
        result = sheets_service.spreadsheets().values().get(spreadsheetId=monitoring_id, range=range_name, majorDimension="ROWS").execute()
        rows = result.get('values', []); num_rows_processed = len(rows)
        print(f"{PURPLE}📉 Ditemukan {num_rows_processed} baris data mentah.{RESET}")
    except HttpError as e: print(f"{PURPLE}❌ Gagal ambil data total: {e}{RESET}"); return {}, 0
    except Exception as e: print(f"{PURPLE}❌ Gagal ambil data total (error tak terduga): {e}{RESET}"); return {}, 0

    categories_in_order = monitoring_header[1:]; totals = {category: 0 for category in categories_in_order}
    header_to_index = {header: i + 1 for i, header in enumerate(categories_in_order)}
    for row_idx, row in enumerate(rows):
        for category, col_index_in_sheet in header_to_index.items():
             col_index_in_row = col_index_in_sheet -1
             if len(row) > col_index_in_row and row[col_index_in_row]:
                 try:
                     value_str = str(row[col_index_in_row]).strip()
                     if value_str: totals[category] += int(value_str)
                 except (ValueError, TypeError): print(f"{PURPLE}⚠ Data tidak valid ('{row[col_index_in_row]}') di baris {row_idx + 2} kolom {chr(ord('A') + col_index_in_sheet -1)} ({category}). Dilewati.{RESET}")
    return totals, num_rows_processed

def delete_data_rows(num_rows):
    """Hapus data mentah (baris 2 sampai num_rows+1) di sheet pertama."""
    if not sheets_service or not monitoring_id or num_rows <= 0: return
    try:
        spreadsheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=monitoring_id).execute()
        if not spreadsheet_metadata.get('sheets'): print(f"{PURPLE}❌ Gagal hapus data: Tidak ada sheet di ID '{monitoring_id}'.{RESET}"); return
        monitoring_sheet_id = spreadsheet_metadata['sheets'][0]['properties']['sheetId']; first_sheet_name = spreadsheet_metadata['sheets'][0]['properties']['title']
        print(f"{PURPLE}🗑 Mempersiapkan hapus {num_rows} baris (2 s/d {num_rows + 1}) dari '{first_sheet_name}'...{RESET}")
        requests = {"requests": [{"deleteDimension": {"range": {"sheetId": monitoring_sheet_id,"dimension": "ROWS","startIndex": 1,"endIndex": 1 + num_rows}}}]}
        sheets_service.spreadsheets().batchUpdate(spreadsheetId=monitoring_id, body=requests).execute()
        print(f"{PURPLE}✅ Berhasil hapus {num_rows} baris data mentah dari '{first_sheet_name}'.{RESET}")
    except HttpError as e: print(f"{PURPLE}❌ Gagal hapus data: {e}{RESET}")
    except Exception as e: print(f"{PURPLE}❌ Gagal hapus data (error tak terduga): {e}{RESET}")

def delete_sheet_by_name(spreadsheet_id, sheet_name_to_delete):
    """Hapus sheet berdasarkan namanya dari spreadsheet yang diberikan."""
    if not sheets_service or not spreadsheet_id: print(f"{PURPLE}❌ Gagal hapus sheet: Service/ID tidak valid.{RESET}"); return
    print(f"{PURPLE}🔍 Mencari Sheet ID '{sheet_name_to_delete}' di ID '{spreadsheet_id}'...{RESET}")
    try:
        spreadsheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet_metadata.get('sheets', []); target_sheet_id = None
        for sheet in sheets:
            if sheet['properties']['title'] == sheet_name_to_delete: target_sheet_id = sheet['properties']['sheetId']; break
        if target_sheet_id is None: print(f"{PURPLE}❌ Gagal hapus: Sheet '{sheet_name_to_delete}' tidak ditemukan di ID '{spreadsheet_id}'.{RESET}"); return
        print(f"{PURPLE}👍 Sheet ID: {target_sheet_id}. Menghapus...{RESET}")
        requests = {'requests': [{'deleteSheet': {'sheetId': target_sheet_id}}]}
        sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=requests).execute()
        print(f"{PURPLE}✅ Berhasil hapus sheet '{sheet_name_to_delete}' (ID: {target_sheet_id}) dari ID '{spreadsheet_id}'.{RESET}")
    except HttpError as e: print(f"{PURPLE}❌ Gagal hapus sheet '{sheet_name_to_delete}': {e}.{RESET}")
    except Exception as e: print(f"{PURPLE}❌ Gagal hapus sheet '{sheet_name_to_delete}' (error tak terduga): {e}{RESET}")

########################################
# SAVE & NOTIFY
########################################
# (save_monitoring_results, mark_monitoring tetap sama)
def save_monitoring_results(results, period):
    """Simpan hasil ke baris berikutnya yang kosong di sheet pertama."""
    if not sheets_service or not monitoring_id: return
    ensure_monitoring_header()
    try:
        spreadsheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=monitoring_id).execute()
        if not spreadsheet_metadata.get('sheets'): print(f"{PURPLE}❌ Gagal simpan hasil: Tidak ada sheet di ID '{monitoring_id}'.{RESET}"); return
        first_sheet_name = spreadsheet_metadata['sheets'][0]['properties']['title']; append_range = f"'{first_sheet_name}'!A:A"
        print(f"{PURPLE}💾 Menyimpan hasil {period} ke '{first_sheet_name}'...{RESET}")
    except HttpError as e: print(f"{PURPLE}❌ Gagal simpan hasil: {e}{RESET}"); return
    except Exception as e: print(f"{PURPLE}❌ Gagal simpan hasil (error tak terduga): {e}{RESET}"); return

    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    row_data = [timestamp] + [results.get(cat, 0) for cat in monitoring_header[1:]]
    try:
        sheets_service.spreadsheets().values().append(spreadsheetId=monitoring_id, range=append_range, valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body={"values": [row_data]}).execute()
        print(f"{PURPLE}✅ Hasil {period} disimpan di '{first_sheet_name}'.{RESET}")
    except HttpError as e: print(f"{PURPLE}❌ Gagal simpan hasil {period}: {e}{RESET}")
    except Exception as e: print(f"{PURPLE}❌ Gagal simpan hasil {period} (error tak terduga): {e}{RESET}")

def mark_monitoring(period):
    """Tambah satu 'M' di kolom Z sheet pertama, baris berikutnya."""
    if not sheets_service or not monitoring_id: return
    try:
        spreadsheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=monitoring_id).execute()
        if not spreadsheet_metadata.get('sheets'): print(f"{PURPLE}❌ Gagal tandai total: Tidak ada sheet di ID '{monitoring_id}'.{RESET}"); return
        first_sheet_name = spreadsheet_metadata['sheets'][0]['properties']['title']; marker_range = f"'{first_sheet_name}'!Z:Z"
        print(f"{PURPLE}🔖 Menambah marker 'M' total {period} di kolom Z '{first_sheet_name}'...{RESET}")
        sheets_service.spreadsheets().values().append(spreadsheetId=monitoring_id, range=marker_range, valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS", body={"values": [["M"]]}).execute()
        print(f"{PURPLE}✅ Marker 'M' total {period} ditambah di kolom Z '{first_sheet_name}'.{RESET}")
    except HttpError as e: print(f"{PURPLE}❌ Gagal tambah marker total: {e}{RESET}")
    except Exception as e: print(f"{PURPLE}❌ Gagal tambah marker total (error tak terduga): {e}{RESET}")


# --- LANGKAH 3: Modifikasi Fungsi Notifikasi ---
async def send_monitoring_notification(results, period, low_interaction_list=None, benchmark=None):
    """
    Kirim notifikasi Telegram. Tambahkan info performa jika ada.

    Args:
        results (dict): Hasil monitoring.
        period (str): Nama periode (Harian, Mingguan, etc.).
        low_interaction_list (list, optional): List string "Nama: Jumlah" yang kurang interaksi.
        benchmark (int, optional): Nilai benchmark yang digunakan.
    """
    if not telegram_token or not telegram_chat_id:
        print(f"{PURPLE}ℹ Token/Chat ID Telegram tidak ada, notifikasi dilewati.{RESET}")
        return

    # 1. Buat Ringkasan Utama
    summary = [f"📊 HASIL MONITORING {period.upper()}"]
    for cat in monitoring_header[1:]:
        summary.append(f"▫ {cat}: {results.get(cat, 0)}")

    # 2. Tambahkan Bagian Performa Rendah (jika ada)
    if low_interaction_list is not None and benchmark is not None and benchmark > 0:
        summary.append(f"\n*📉 PERFORMA DI BAWAH BENCHMARK ({benchmark})*")
        if low_interaction_list:
            summary.append("Anggota/Kategori berikut perlu peningkatan:👇")
            # Tambahkan list dengan format bullet point
            for item in low_interaction_list:
                 summary.append(f"- {item}") # item sudah dalam format "Nama: Jumlah"
        else:
            summary.append("✅ Semua anggota/kategori mencapai atau melebihi benchmark!")
    elif period.upper() == "HARIAN": # Jika harian tapi tidak ada data low_interaction (misal benchmark 0)
         summary.append(f"\n*📉 PERFORMA DI BAWAH BENCHMARK*")
         summary.append("ℹ Tidak ada data performa atau benchmark 0.")


    # 3. Kirim Pesan
    try:
        bot = Bot(telegram_token)
        message = "\n".join(summary)
        send_tasks = [] # Kumpulkan task pengiriman

        if thread_ids:
            print(f"{PURPLE}✉ Mengirim notifikasi {period} ke Telegram Chat ID {telegram_chat_id} (Threads: {thread_ids})...{RESET}")
            for tid in thread_ids:
                # Buat task untuk setiap pengiriman
                send_tasks.append(
                    bot.send_message(chat_id=telegram_chat_id, text=message, parse_mode="Markdown", message_thread_id=tid)
                )
            # Jalankan semua task secara bersamaan
            results = await asyncio.gather(*send_tasks, return_exceptions=True)

            # Hitung sukses/gagal
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            failed_count = len(results) - success_count
            if success_count > 0 : print(f"{PURPLE}✅ Notifikasi {period} berhasil dikirim ke {success_count} thread Telegram.{RESET}")
            if failed_count > 0 :
                print(f"{PURPLE}❌ Gagal kirim notifikasi {period} ke {failed_count} thread Telegram.{RESET}")
                # Log error spesifik jika perlu
                for i, r in enumerate(results):
                    if isinstance(r, Exception): print(f"   - Thread ID {thread_ids[i]}: {r}")

        else:
            print(f"{PURPLE}✉ Mengirim notifikasi {period} ke Telegram Chat ID {telegram_chat_id}...{RESET}")
            await bot.send_message(chat_id=telegram_chat_id, text=message, parse_mode="Markdown")
            print(f"{PURPLE}✅ Notifikasi {period} berhasil dikirim ke Telegram.{RESET}")

    except Exception as e:
        print(f"{PURPLE}❌ Gagal mengirim notifikasi Telegram: {e}{RESET}")


########################################
# MAIN LOGIC & MENU
########################################

# --- LANGKAH 2: Modifikasi run_monitoring ---
def run_monitoring(period, categories):
    """Jalankan monitoring & kirim notifikasi (termasuk cek performa harian)."""
    print(f"\n{PURPLE}--- Memulai Monitoring {period} ---{RESET}")
    if not sheets_service: print(f"{PURPLE}❌ Gagal: Layanan Google Sheets tidak tersedia.{RESET}"); return

    # 1. Dapatkan hasil monitoring
    results = monitor_categories(categories)
    print(f"{PURPLE}📊 Hasil Monitoring {period}: {results}{RESET}")

    # 2. Simpan hasil ke sheet
    save_monitoring_results(results, period)

    # 3. Cek performa & siapkan notifikasi (KHUSUS HARIAN)
    low_interaction_data = None
    benchmark_value_data = None
    if period.upper() == "HARIAN":
        # Panggil helper untuk cek performa
        low_interaction_data, benchmark_value_data = find_low_interaction(
            results,
            daily_categories, # Periksa semua kategori harian
            BENCHMARK_CATEGORIES # Gunakan kategori patokan yang sudah didefinisikan
        )

    # 4. Kirim notifikasi (lewatkan data performa jika ada)
    asyncio.run(send_monitoring_notification(
        results,
        period,
        low_interaction_list=low_interaction_data,
        benchmark=benchmark_value_data
    ))
    print(f"{PURPLE}--- Monitoring {period} Selesai ---{RESET}")

# (run_total_monitoring, run_delete_sheet tetap sama)
def run_total_monitoring():
    """Jalankan monitoring total dan bersihkan data mentah."""
    print(f"\n{PURPLE}--- Memulai Perhitungan Total & Pembersihan Data ---{RESET}")
    if not sheets_service: print(f"{PURPLE}❌ Gagal: Layanan Google Sheets tidak tersedia.{RESET}"); return

    totals, num_data_rows = calculate_total_monitoring()

    if not totals and num_data_rows == 0 and not any(read_file("monitoringid.txt")):
        print(f"{PURPLE}❌ Hitung total gagal/tidak ada data.{RESET}"); print(f"{PURPLE}--- Hitungan Total Gagal ---{RESET}"); return
    elif not totals and num_data_rows > 0: print(f"{PURPLE}⚠ Hitung total kosong meski ada {num_data_rows} baris. Cek format data.{RESET}")

    print(f"{PURPLE}📊 Total: {totals}{RESET}")
    save_monitoring_results(totals, "TOTAL")
    if num_data_rows > 0: delete_data_rows(num_data_rows)
    else: print(f"{PURPLE}ℹ Tidak ada data mentah untuk dihapus.{RESET}")
    mark_monitoring("TOTAL")
    asyncio.run(send_monitoring_notification(totals, "TOTAL")) # Kirim notif total biasa
    print(f"{PURPLE}--- Perhitungan Total & Pembersihan Selesai ---{RESET}")

def run_delete_sheet():
    """Meminta nama sheet dan menghapusnya dari spreadsheet Monitoring."""
    print(f"\n{PURPLE}--- Hapus Sheet di Spreadsheet Monitoring ---{RESET}")
    if not sheets_service or not monitoring_id: print(f"{PURPLE}❌ Tidak dapat hapus sheet: Service/ID Monitoring tidak valid.{RESET}"); return
    sheet_name = input(f"{WHITE}Masukkan nama sheet yang ingin dihapus (case-sensitive): {RESET}").strip()
    if not sheet_name: print(f"{PURPLE}❌ Nama sheet kosong.{RESET}"); return
    confirm = input(f"{PURPLE}⚠ Yakin hapus sheet '{sheet_name}' PERMANEN dari ID {monitoring_id}? (y/n): {RESET}").strip().lower()
    if confirm == 'y': delete_sheet_by_name(monitoring_id, sheet_name)
    else: print(f"{PURPLE}ℹ Penghapusan sheet dibatalkan.{RESET}")
    print(f"{PURPLE}--- Proses Hapus Sheet Selesai ---{RESET}")

# (menu tetap sama strukturnya, hanya pemanggilan run_monitoring yg otomatis menangani fitur baru)
def menu():
    if not sheets_service or not monitoring_id: print(f"{PURPLE}❌ Tidak dapat memulai menu.{RESET}"); return
    ensure_monitoring_header()
    while True:
        daily_cats_str = ', '.join(daily_categories); weekly_cats_str = ', '.join(weekly_categories); monthly_cats_str = ', '.join(monthly_categories)
        if len(daily_cats_str) > 60: daily_cats_str = ', '.join(daily_categories[:8]) + '...'
        print(f"""{PURPLE}
-------------------------------- MENU UTAMA --------------------------------
[1] Jalankan Monitoring Harian  (Kategori: {daily_cats_str}) [+ Cek Performa]
[2] Jalankan Monitoring Mingguan (Kategori: {weekly_cats_str})
[3] Jalankan Monitoring Bulanan (Kategori: {monthly_cats_str})
[4] HITUNG TOTAL SEMUA DATA & Bersihkan Data Mentah
[5] HAPUS SHEET di Spreadsheet Monitoring (ID: {monitoring_id})
[6] Keluar
--------------------------------------------------------------------------
{RESET}""")
        choice = input(f"{WHITE}Pilih opsi [1-6]: {RESET}").strip()
        if choice == "1": run_monitoring("Harian", daily_categories) # Otomatis cek performa
        elif choice == "2": run_monitoring("Mingguan", weekly_categories)
        elif choice == "3": run_monitoring("Bulanan", monthly_categories)
        elif choice == "4": run_total_monitoring()
        elif choice == "5": run_delete_sheet()
        elif choice == "6": print(f"{PURPLE}🔚 Program selesai.{RESET}"); break
        else: print(f"{PURPLE}❌ Pilihan tidak valid! [1-6].{RESET}")
        input(f"\n{WHITE}Tekan Enter untuk kembali ke menu...{RESET}")

if __name__ == "__main__":
    print(PURPLE + "============================== PERHATIAN ==============================" + RESET)
    print(PURPLE + "Pastikan 'mospreadsheet_id.txt' sudah update untuk semua anggota." + RESET)
    print(PURPLE + "Patokan performa harian: Max(Reshareshing, Analysis, Strategy)." + RESET) # Info tambahan
    print(PURPLE + "=======================================================================" + RESET)
    input(f"{WHITE}Tekan Enter untuk melanjutkan...{RESET}")
    try:
        if sheets_service and monitoring_id: menu()
        else: print(f"{PURPLE}❌ Program tidak dapat dilanjutkan.{RESET}")
    except KeyboardInterrupt: print(f"\n{PURPLE}⌨ Program dihentikan (Ctrl+C).{RESET}")
    except Exception as e: print(f"\n{PURPLE}💥 Error tidak terduga: {e}{RESET}")
