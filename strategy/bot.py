import datetime
from textwrap import dedent
import requests
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Warna terminal – menggunakan biru untuk output lainnya, sedangkan logo akan dicetak dengan putih.
BLUE = "\033[94m"
WHITE = "\033[97m"
RESET = "\033[0m"

########################################
# FUNGSI UNTUK MENAMPILKAN LOGO
########################################
def tampilkan_logo():
    width = 80  # Lebar tampilan yang diinginkan
    # Gunakan raw string (r""") untuk menghindari escape sequence warning
    logo = dedent(rf"""{WHITE}

██████  ██████   ██████  ██████  ██   ██      ██ ██    ██ ███    ██  ██████  ██      ███████ ██████
██   ██ ██   ██ ██    ██ ██   ██  ██ ██       ██ ██    ██ ████   ██ ██       ██      ██      ██   ██
██   ██ ██████  ██    ██ ██████    ███        ██ ██    ██ ██ ██  ██ ██   ███ ██      █████   ██████
██   ██ ██   ██ ██    ██ ██       ██ ██  ██   ██ ██    ██ ██  ██ ██ ██    ██ ██      ██      ██   ██
██████  ██   ██  ██████  ██      ██   ██  █████   ██████  ██   ████  ██████  ███████ ███████ ██   ██

                                            STRATEGY TOOLS


{RESET}""")
    print(logo)

########################################
# UTILITAS DAN TAMPILAN
########################################

def read_file(filename):
    """Membaca file konfigurasi dan mengembalikan isinya sebagai string (trim spasi)."""
    try:
        with open(filename, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"❌ Gagal membaca {filename}: {e}")
        return None

def garis():
    print("=" * 60)

def header(text):
    garis()
    print(f"{text:^60}")
    garis()

def display_anti_sybil():
    anti_sybil_text = dedent("""\
    🔍 Reminder - Panduan Terhindar dari Sybil:
    - Punya identitas dan transaksi di blockchain sebagai pengguna aktif (opsional)
    - Pakai VPN/Proxy untuk merubah IP address yang berbeda setiap ganti akun
    - Gunakan emulator untuk mengganti ID device dan merk (jika di PC)
      atau download browser berbeda di HP jika akun banyak
    - Dilarang keras kirim ke sesama teman atau ke diri sendiri
    """)
    print("\n" + anti_sybil_text)
    garis()
    return anti_sybil_text

def display_steps():
    steps = {
        "1": "Swap",
        "2": "Bridge",
        "3": "Delegasi",
        "4": "Faucet",
        "5": "Mint NFT",
        "6": "Deploy",
        "7": "Staking",
        "8": "Supply and Borrow",
        "9": "Trade",
        "10": "Check in",
        "11": "Tugas Twitter",
        "12": "Tugas Telegram",
        "13": "Push role Discord",
        "14": "node testnet"
    }
    print("📋 Langkah-Langkah Mengerjakan Tugas (Pilih Tipe Umum):") # Ubah teks header
    print("(Wajib otorisasi akun sosmed dan connect wallet blockchain)\n")
    for key in sorted(steps.keys(), key=lambda x: int(x)):
        print(f"[{key:>2}] {steps[key]}")
    print()
    return steps

def print_summary_box(lines):
    if not lines:
        return
    max_length = max(len(line) for line in lines)
    border = "=" * (max_length + 4)
    print(BLUE + border)
    for line in lines:
        print("| " + line.ljust(max_length) + " |")
    print(border + RESET)

########################################
# TELEGRAM PENGIRIMAN
########################################

def send_to_telegram(message, bot_token, chat_id, thread_id=None):
    """
    Mengirim pesan ke Telegram Supergroup menggunakan Bot API.
    Jika thread_id disediakan, pesan akan dikirim ke thread tertentu.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    if thread_id is not None:
        payload["message_thread_id"] = thread_id

    response = requests.post(url, data=payload)
    if response.status_code == 200:
        print(BLUE + "✅ Data berhasil dikirim ke Telegram." + RESET)
    else:
        print(BLUE + "❌ Gagal mengirim data ke Telegram:", response.text + RESET)

########################################
# GOOGLE SHEETS PENGIRIMAN
########################################

# PERHATIAN: Fungsi ini perlu diubah untuk menampung kolom baru 'Deskripsi Langkah Spesifik'
# Anda perlu menyesuaikan header_list, range, dan index kolom
def send_to_sheets(record, sheet_name):
    """
    Mengirim data ke Google Sheets menggunakan Google Sheets API.
    Record: list dengan elemen sesuai header (sekarang 5 elemen jika ditambah Deskripsi).
    Contoh Header yang diperbarui: ["Timestamp", "Nama Airdrop", "StepbyStep (Tipe)", "Deskripsi Langkah Spesifik", "Feedback"]
    Data baru ditulis pada baris genap (A2:E2, A4:E4, dst.)
    Marker "M" akan ditambahkan di kolom Y pada baris yang sama.
    """
    spreadsheet_id = read_file("spreadsheet_id.txt")
    if not spreadsheet_id:
        print("❌ Spreadsheet ID tidak ditemukan.")
        return

    # Inisialisasi Google Sheets API
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

    # Dapatkan direktori script saat ini
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Dapatkan direktori induk, yaitu folder DROPXJUNGLER
    parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

    # Susun path lengkap ke file credentials.json di folder induk
    credentials_path = os.path.join(parent_dir, 'credentials.json')

    try:
        # Muat kredensial dari file di folder induk
        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES)
        sheets_service = build('sheets', 'v4', credentials=creds)
    except Exception as e:
        print(f"❌ Gagal memuat kredensial atau membuat service Sheets: {e}")
        return

    # =====================================================================
    # BAGIAN INI PERLU DIUBAH SESUAI DENGAN JUMLAH KOLOM BARU DI RECORD
    # Contoh untuk 5 kolom: ["Timestamp", "Nama Airdrop", "StepbyStep (Tipe)", "Deskripsi Langkah Spesifik", "Feedback"]
    header_list = ["Timestamp", "Nama Airdrop", "StepbyStep (Tipe)", "Deskripsi Langkah Spesifik", "Feedback"] # <-- PERBARUI INI
    header_range = f"{sheet_name}!A1:E1" # <-- SESUAIKAN RANGE HEADER
    # =====================================================================

    try:
        result = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=header_range).execute()
        values = result.get("values", [])
        if not values or values[0] != header_list:
            body = {"values": [header_list]}
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=header_range,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            print(BLUE + f"Header berhasil ditulis/diperbarui di {header_range}." + RESET)
            data_count = 0
        else:
            # Hitung jumlah baris data yang ada (berdasarkan kolom pertama A)
            data_range = f"{sheet_name}!A2:A" # <-- Tetap A, karena ini kolom pertama
            result = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=data_range).execute()
            values = result.get("values", [])
            data_count = len([row for row in values if row and row[0].strip() != ""])

        next_data_row = 2 * (data_count + 1)

        # =====================================================================
        # BAGIAN INI PERLU DIUBAH UNTUK RANGE DATA BARU
        update_range = f"{sheet_name}!A{next_data_row}:E{next_data_row}" # <-- SESUAIKAN RANGE DATA
        # =====================================================================

        body_data = {"values": [record]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=update_range,
            valueInputOption="USER_ENTERED",
            body=body_data
        ).execute()
        print(BLUE + f"Data berhasil ditulis di {update_range}." + RESET)

        # Marker 'M' tetap di kolom Y pada baris yang sama
        marker_range = f"{sheet_name}!Y{next_data_row}:Y{next_data_row}"
        body_marker = {"values": [["M"]]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=marker_range,
            valueInputOption="USER_ENTERED",
            body=body_marker
        ).execute()
        print(BLUE + f"Marker 'M' berhasil ditambahkan di {marker_range}" + RESET)

    except Exception as e:
        print(f"❌ Gagal mengirim data ke Google Sheets: {e}")


########################################
# MAIN PROGRAM
########################################

def main():
    # Tampilkan logo di awal program
    tampilkan_logo()

    # Baca konfigurasi dari file
    bot_token = read_file("token.txt")
    chat_id = read_file("idchat.txt")
    thread_id_text = read_file("threads.txt")
    thread_id = int(thread_id_text) if thread_id_text and thread_id_text.isdigit() else None

    if not all([bot_token, chat_id]):
        print("❌ Konfigurasi tidak lengkap. Pastikan token.txt dan idchat.txt sudah ada.")
        return

    airdrop_name = input(BLUE + "\n🛎  Masukkan Nama Airdrop: " + RESET)

    anti_sybil_choice = input(BLUE + "\n⚠  Perlu melihat panduan anti sybil? [y/n]: " + RESET).strip().lower() # Ubah teks pertanyaan biar lebih jelas
    if anti_sybil_choice == "y":
        input(BLUE + "\n🚨 Tekan Enter untuk melihat panduan anti sybil..." + RESET)
        anti_sybil_message = display_anti_sybil()
        paham = input(BLUE + "\n✅ Apakah anda paham panduan anti sybil? [y/n]: " + RESET).strip().lower() # Tambah konfirmasi paham anti-sybil
        if paham != "y":
            print(BLUE + "\n❌ Silakan pelajari panduan anti sybil dan coba lagi." + RESET)
            return
    else:
        anti_sybil_message = ""

    print(BLUE + "\n🔗 Pastikan Anda telah:" + RESET)
    print(BLUE + "- Otorisasi akun sosial media" + RESET)
    print(BLUE + "- Connect wallet blockchain\n" + RESET)
    input(BLUE + "Tekan Enter jika sudah siap mencatat langkah..." + RESET) # Tambah jeda agar user siap

    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    steps = display_steps()
    selected_steps_input = input(BLUE + "🔢 Masukkan nomor tipe langkah umum sebagai referensi (pisahkan dengan koma): " + RESET) # Ubah teks pertanyaan
    selected_step_keys = [s.strip() for s in selected_steps_input.split(",") if s.strip() in steps]
    selected_step_names = [steps[key] for key in selected_step_keys]

    # ====== TAMBAHAN INPUT BARU UNTUK DESKRIPSI DETAIL ======
    print(BLUE + "\n📝 Sekarang, deskripsikan langkah-langkah spesifik yang Anda lakukan untuk airdrop ini." + RESET)
    print(BLUE + "(Contoh: 'Swap USDC ke ETH di Uniswap (jaringan Arbitrum), lalu Bridge ETH dari Arbitrum ke Optimism pakai Hop Protocol, Mint NFT gratis di situs proyek, lalu Daily Check-in di Galxe.')" + RESET)
    detailed_steps = input(BLUE + ">>> Masukkan Deskripsi Langkah Spesifik: " + RESET)
    # =======================================================

    feedback = input(BLUE + "\n💬 Masukkan Feedback / Catatan Lainnya: " + RESET) # Ubah teks feedback biar jelas beda dgn deskripsi

    # Tampilkan ringkasan di terminal (tambahkan deskripsi detail)
    header(" DropXJungler Strategy Tools ")
    print(f"{'Timestamp :':<25} {now}")
    print(f"{'Nama Airdrop:':<25} {airdrop_name}")
    print(f"{'Tipe Langkah (Umum):':<25} {', '.join(selected_step_names)}") # Ubah teks display
    print(f"{'Deskripsi Langkah Spesifik:':<25} {detailed_steps}") # Tampilkan deskripsi detail
    print(f"{'Feedback / Catatan:':<25} {feedback}") # Ubah teks display
    garis()

    # Buat payload record untuk Spreadsheet (sekarang 5 kolom)
    # Urutkan sesuai dengan header_list di fungsi send_to_sheets
    record = [now, airdrop_name, ', '.join(selected_step_names), detailed_steps, feedback] # <-- TAMBAHKAN detailed_steps

    # Buat pesan ringkasan untuk Telegram dalam format Markdown (sertakan deskripsi detail)
    telegram_message = dedent(f"""
    DropXJungler Strategy Tools - Laporan Tugas Baru

    Timestamp: {now}
    Nama Airdrop: {airdrop_name}
    Tipe Langkah (Umum): {', '.join(selected_step_names) if selected_step_names else 'Tidak ada tipe dipilih'}
    Deskripsi Langkah Spesifik:
    {detailed_steps if detailed_steps else 'Tidak ada deskripsi spesifik'}

    Feedback / Catatan: {feedback if feedback else 'Tidak ada feedback'}

    ---
    {anti_sybil_message}
    """)

    final_choice = input(BLUE + "\nApakah anda yakin ingin mengirim data ini? [y/n]: " + RESET).strip().lower() # Ubah teks konfirmasi
    if final_choice == "y":
        send_to_telegram(telegram_message, bot_token, chat_id, thread_id)
        # Pastikan Google Sheet Anda sudah punya kolom baru untuk "Deskripsi Langkah Spesifik"
        # sebelum menjalankan ini, dan sesuaikan fungsi send_to_sheets jika perlu (sudah ditandai di atas)
        send_to_sheets(record, "Strategy") # Sheet name "Strategy" as per original code
    else:
        print(BLUE + "Pengiriman data dibatalkan." + RESET)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Saat Ctrl+C ditekan, tampilkan pesan dan keluar tanpa traceback
        print(f"\n{BLUE}Program dihentikan oleh pengguna.{RESET}")
