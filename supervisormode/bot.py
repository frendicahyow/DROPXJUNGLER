import os
import subprocess
import datetime
import collections
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from colorama import init, Fore, Style

# Inisialisasi Colorama
init(autoreset=True)

# ====================================================
# KONFIGURASI GLOBAL
# ====================================================
BASE_DIR = os.path.expanduser("~/DROPXJUNGLER")
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))

# Inisialisasi Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Dapatkan direktori script saat ini (misal: DROPXJUNGLER/reshareshing)
script_dir = os.path.dirname(os.path.realpath(__file__))

# Dapatkan direktori induk, yaitu folder DROPXJUNGLER
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

# Susun path lengkap ke file credentials.json di folder induk
credentials_path = os.path.join(parent_dir, 'credentials.json')

# Muat kredensial dari file di folder induk
creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=creds)

# ----------------------------------------------------
# BAGIAN 1 & 2: Opsi 1 dan 2 (tidak diubah)
# ----------------------------------------------------
SCRIPTS = {
    1: 'reshareshing',
    2: 'analisa',
    3: 'strategy',
    4: 'moderator',
    5: 'scriptinfo',
    6: 'data curator',
    7: 'monitoring',
    8: 'proofwork'
}
DISPLAY_NAMES = {
    1: '1. Reshareshing',
    2: '2. Analysis',
    3: '3. Strategy',
    4: '4. Moderator',
    5: '5. ScriptInfo',
    6: '6. DataCurator',
    7: '7. Monitoring',
    8: '8. ProofWork (Tidak dijalankan otomatis)'
}

def get_credentials(dir_name):
    creds_path = os.path.join(BASE_DIR, dir_name, 'credentials.json')
    try:
        creds = service_account.Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        return creds
    except Exception as e:
        print(f"Error credentials di {dir_name}: {str(e)}")
        return None

def run_script(numbers=None):
    if numbers is None:
        print("\nDaftar Script Tersedia:")
        for num in sorted(DISPLAY_NAMES.keys()):
            print(DISPLAY_NAMES[num])
        selected = input("\nMasukkan nomor script (pisahkan dengan koma): ")
        numbers = [int(n.strip()) for n in selected.split(',')]
    print("\n⏳ Memulai proses eksekusi script...")
    for num in numbers:
        dir_name = SCRIPTS.get(num)
        if not dir_name:
            print(f"✗ Nomor script {num} tidak valid")
            continue
        script_path = os.path.join(BASE_DIR, dir_name)
        if not os.path.isdir(script_path):
            print(f"✗ Folder '{dir_name}' tidak ditemukan di {BASE_DIR}.")
            continue
        print(f"\n➤ Menjalankan {DISPLAY_NAMES[num]}...")
        try:
            subprocess.run(
                ['python', 'bot.py'],
                cwd=script_path,
                check=True,
                start_new_session=True
            )
            print(f"✓ {DISPLAY_NAMES[num]} berhasil dijalankan")
        except KeyboardInterrupt:
            if num == 6:
                print(f"✗ {DISPLAY_NAMES[num]} dihentikan oleh pengguna (KeyboardInterrupt). Lanjut ke script berikutnya...")
                continue
            else:
                raise
        except subprocess.CalledProcessError as e:
            if num == 6 and e.returncode == 2:
                print(f"✗ {DISPLAY_NAMES[num]} dihentikan oleh pengguna (exit code 2). Lanjut ke script berikutnya...")
                continue
            else:
                print(f"✗ Gagal menjalankan {DISPLAY_NAMES[num]}: {str(e)}")
        except Exception as e:
            print(f"✗ Gagal menjalankan {DISPLAY_NAMES[num]}: {str(e)}")
    print("\n✅ Proses eksekusi selesai!")
    input("\nTekan Enter untuk melanjutkan...")

# ----------------------------------------------------
# BAGIAN 3: Salin Data ke Sheet Baru (Data Curator)
# ----------------------------------------------------
def read_sheet_ids(file_path):
    mapping = collections.defaultdict(list)
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(':')
            if len(parts) == 2:
                sheet_name = parts[0].strip()
                spreadsheet_id = parts[1].strip()
                mapping[spreadsheet_id].append(sheet_name)
    return mapping

def read_supervisor_id(file_path):
    with open(file_path, 'r') as f:
        return f.read().strip()

def print_header(title):
    print("=" * 60)
    print(f"{title}".center(60))
    print("=" * 60)

def copy_data():
    creds = service_account.Credentials.from_service_account_file(
        os.path.join(LOCAL_DIR, 'credentials.json'), scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=creds)
    sheetid_mapping = read_sheet_ids(os.path.join(LOCAL_DIR, 'sheetid.txt'))
    destination_spreadsheet_id = read_supervisor_id(os.path.join(LOCAL_DIR, 'idsupervisor.txt'))
    
    print_header("PROSES PENYALINAN SHEET")
    print(f"Spreadsheet Tujuan: {destination_spreadsheet_id}")
    print(f"Waktu Mulai: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    for source_spreadsheet_id, info_names in sheetid_mapping.items():
        try:
            source_info = service.spreadsheets().get(spreadsheetId=source_spreadsheet_id).execute()
            sheets = source_info.get('sheets', [])
            sheet_titles = [s['properties']['title'] for s in sheets]
            
            print("-" * 60)
            print(f"Memproses Spreadsheet ID: {source_spreadsheet_id}")
            print(f"Sheet yang ditemukan: {', '.join(sheet_titles)}")
            print("-" * 60)
            
            for sheet in sheets:
                sheet_id = sheet['properties']['sheetId']
                sheet_title = sheet['properties']['title']
                copy_response = service.spreadsheets().sheets().copyTo(
                    spreadsheetId=source_spreadsheet_id,
                    sheetId=sheet_id,
                    body={'destinationSpreadsheetId': destination_spreadsheet_id}
                ).execute()
                print(f"[SUCCESS] Sheet '{sheet_title}' (sheetId: {sheet_id}) berhasil disalin.")
            print("")
        except Exception as e:
            print(f"[ERROR] Kesalahan saat memproses spreadsheet {source_spreadsheet_id}: {e}")
    
    print_header("PROSES SELESAI")
    print(f"Waktu Selesai: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    input("Tekan Enter untuk kembali ke menu utama...")

# ----------------------------------------------------
# BAGIAN 4: Monitoring
# ----------------------------------------------------
def print_monitoring_header():
    header_text = f"""
{Fore.CYAN}{Style.BRIGHT}
╔════════════════════════════════════════════════════════════════
║                      SYSTEM MONITORING REPORT                  
╠════════════════════════════════════════════════════════════════
║ Date: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"):<40}║
╚════════════════════════════════════════════════════════════════
{Style.RESET_ALL}
"""
    print(header_text)

def get_service_local():
    creds = service_account.Credentials.from_service_account_file(
        os.path.join(LOCAL_DIR, 'credentials.json'), scopes=SCOPES)
    return build('sheets', 'v4', credentials=creds)

def get_supervisor_spreadsheet_id_monitor():
    file_name = os.path.join(LOCAL_DIR, 'idsupervisor.txt')
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            spreadsheet_id = f.read().strip()
            if spreadsheet_id:
                return spreadsheet_id
    raise Exception("File idsupervisor.txt tidak ditemukan atau kosong.")

def get_sheet_ids_monitor():
    mapping = {}
    file_name = os.path.join(LOCAL_DIR, 'sheetid.txt')
    if os.path.exists(file_name):
        with open(file_name, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if ':' in line:
                    key, value = line.split(':', 1)
                    mapping[key.strip()] = value.strip()
    else:
        raise Exception("File sheetid.txt tidak ditemukan.")
    return mapping

def get_column_data(service, spreadsheet_id, range_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    return result.get('values', [])

def count_m_in_data(data):
    total = 0
    for row in data:
        for cell in row:
            total += cell.lower().count('m')
    return total

def ensure_supervisor_sheet_exists(service, spreadsheet_id, sheet_title):
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    for sheet in sheets:
        title = sheet.get('properties', {}).get('title', '')
        if title.lower() == sheet_title.lower():
            return
    body = {
        'requests': [{
            'addSheet': {
                'properties': {
                    'title': sheet_title,
                    'gridProperties': {
                        'rowCount': 1000,
                        'columnCount': 20
                    }
                }
            }
        }]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()
    print(f"{Fore.GREEN}Sheet '{sheet_title}' telah dibuat pada spreadsheet target.{Style.RESET_ALL}")

def append_results(service, spreadsheet_id, range_name, header, data_row):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])
    if not values:
        body = {'values': [header]}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
    body = {'values': [data_row]}
    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()
    print(f"{Fore.MAGENTA}Data monitoring telah disimpan ke spreadsheet target.{Style.RESET_ALL}")

def update_total_row(service, spreadsheet_id, sheet_title, monitored_sheets):
    range_all = f"{sheet_title}!A:Z"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_all
    ).execute()
    all_rows = result.get('values', [])
    if len(all_rows) < 2:
        print(f"{Fore.YELLOW}Tidak ada data baris untuk dijumlahkan.{Style.RESET_ALL}")
        return
    header = all_rows[0]
    num_columns = len(header)
    data_rows = [row for row in all_rows[1:] if row and "T" in row[0]]
    if not data_rows:
        print(f"{Fore.YELLOW}Tidak ada data baris untuk dijumlahkan.{Style.RESET_ALL}")
        return
    totals = [0] * (num_columns - 1)
    for row in data_rows:
        for i in range(1, num_columns):
            try:
                value = int(row[i]) if i < len(row) else 0
            except ValueError:
                value = 0
            totals[i - 1] += value
    total_timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    total_row = [total_timestamp] + totals
    clear_range = f"{sheet_title}!A2:Z"
    service.spreadsheets().values().clear(
         spreadsheetId=spreadsheet_id,
         range=clear_range,
         body={}
    ).execute()
    body = {'values': [total_row]}
    service.spreadsheets().values().append(
         spreadsheetId=spreadsheet_id,
         range=f"{sheet_title}!A2",
         valueInputOption='RAW',
         body=body
    ).execute()
    print(f"{Fore.BLUE}Data monitoring lama telah dihapus dan baris total baru telah ditambahkan.{Style.RESET_ALL}")

def monitoring():
    print_monitoring_header()
    service = get_service_local()
    supervisor_spreadsheet_id = get_supervisor_spreadsheet_id_monitor()
    mapping = get_sheet_ids_monitor()
    monitored_sheets = [
        "Reshareshing", "Analysis", "Strategy", "Moderator",
        "Datacurator", "listairdrop", "Dimas", "Agung",
        "Anang", "Tayong", "Agus", "Frendi", "Ulan", "Monitoring"
    ]
    supervisor_sheet_title = "supervisormonitoring"
    supervisor_range = f"{supervisor_sheet_title}!A:Z"
    ensure_supervisor_sheet_exists(service, supervisor_spreadsheet_id, supervisor_sheet_title)
    results = []
    print(f"{Fore.CYAN}{Style.BRIGHT}Mengambil data monitoring...{Style.RESET_ALL}")
    for sheet_name in monitored_sheets:
        sheet_id = mapping.get(sheet_name)
        if not sheet_id:
            print(f"{Fore.RED}ID untuk sheet '{sheet_name}' tidak ditemukan di sheetid.txt. Lewati.{Style.RESET_ALL}")
            results.append("N/A")
            continue
        if sheet_name.lower() == "datacurator":
            column = "AY"
        elif sheet_name.lower() == "monitoring":
            column = "Z"
        else:
            column = "Y"
        data_range = f"{sheet_name}!{column}:{column}"
        try:
            data = get_column_data(service, sheet_id, data_range)
            m_count = count_m_in_data(data)
            print(f"{Fore.GREEN}Sheet '{sheet_name}': jumlah 'm' = {m_count}{Style.RESET_ALL}")
            results.append(m_count)
        except Exception as e:
            print(f"{Fore.RED}Gagal mengambil data dari sheet '{sheet_name}': {e}{Style.RESET_ALL}")
            results.append("Error")
    header = ["Timestamp"] + monitored_sheets
    timestamp = datetime.datetime.now().isoformat()
    data_row = [timestamp] + results
    append_results(service, supervisor_spreadsheet_id, supervisor_range, header, data_row)
    confirm = input(f"{Fore.YELLOW}Apakah Anda ingin menghitung total dan menghapus data monitoring lama? (y/n): {Style.RESET_ALL}")
    if confirm.lower() == 'y':
        update_total_row(service, supervisor_spreadsheet_id, supervisor_sheet_title, monitored_sheets)
    input("Tekan Enter untuk kembali ke menu utama...")

# ----------------------------------------------------
# BAGIAN 5: Clear Data Utility - Supervisor & Role
# ----------------------------------------------------
def print_clear_banner():
    banner = f"""
{Fore.CYAN}{'='*60}
{'CLEAR DATA UTILITY - SUPERVISOR & ROLE'.center(60)}
{'='*60}{Style.RESET_ALL}
"""
    print(banner)

def get_credentials_clear():
    try:
        creds = service_account.Credentials.from_service_account_file(
            os.path.join(LOCAL_DIR, 'credentials.json'), scopes=SCOPES)
        print(Fore.GREEN + "[INFO] Credentials berhasil didapatkan.")
        return creds
    except Exception as e:
        print(Fore.RED + f"[ERROR] Gagal mendapatkan credentials: {e}")
        exit(1)

def read_supervisor_id_clear(filename='idsupervisor.txt'):
    try:
        with open(os.path.join(LOCAL_DIR, filename), 'r') as f:
            supervisor_id = f.read().strip()
        print(Fore.GREEN + f"[INFO] ID Supervisor: {supervisor_id}")
        return supervisor_id
    except Exception as e:
        print(Fore.RED + f"[ERROR] Gagal membaca {filename}: {e}")
        exit(1)

def read_sheet_ids_clear(filename='sheetid.txt'):
    sheet_ids = {}
    try:
        with open(os.path.join(LOCAL_DIR, filename), 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if ':' in line:
                    key, value = line.split(':', 1)
                    sheet_ids[key.strip()] = value.strip()
                else:
                    sheet_ids[line.strip()] = line.strip()
        print(Fore.GREEN + f"[INFO] Ditemukan {len(sheet_ids)} spreadsheet di {filename}.")
        return sheet_ids
    except Exception as e:
        print(Fore.RED + f"[ERROR] Gagal membaca {filename}: {e}")
        exit(1)

def clear_supervisor_sheets_util(service, spreadsheet_id):
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    sheet_titles = [sheet['properties']['title'] for sheet in sheets]
    print(Fore.YELLOW + "\nSupervisor Spreadsheet memiliki sheet berikut:")
    for title in sheet_titles:
         print(Fore.YELLOW + f" - {title}")
    confirm = input(Fore.MAGENTA + "\nApakah Anda yakin ingin menghapus semua sheet (selain sheet kosong baru) di spreadsheet ini? (y/n): " + Style.RESET_ALL)
    if confirm.lower() != 'y':
         print(Fore.CYAN + "Operasi dibatalkan.")
         return
    if len(sheets) == 1:
         add_request = {
             "addSheet": {
                 "properties": {
                     "title": "Blank"
                 }
             }
         }
         service.spreadsheets().batchUpdate(
             spreadsheetId=spreadsheet_id,
             body={"requests": [add_request]}
         ).execute()
         print(Fore.GREEN + "Ditambahkan sheet 'Blank' karena hanya ada satu sheet.")
         spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
         sheets = spreadsheet
