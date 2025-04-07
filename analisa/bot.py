import os
import datetime
import asyncio
import requests
from textwrap import dedent
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Warna terminal (ANSI escape codes)
GREEN = "\033[92m"
WHITE = "\033[97m"
RESET = "\033[0m"

########################################
# KONFIGURASI & UTILITAS
########################################

def load_config():
    config = {"token": "", "chat_id": "", "thread_ids": []}
    try:
        with open("token.txt", "r") as f:
            config["token"] = f.read().strip()
    except Exception as e:
        print(GREEN + "Error reading token.txt: " + str(e) + RESET)
    try:
        with open("idchat.txt", "r") as f:
            config["chat_id"] = f.read().strip()
    except Exception as e:
        print(GREEN + "Error reading idchat.txt: " + str(e) + RESET)
    try:
        with open("threads.txt", "r") as f:
            config["thread_ids"] = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(GREEN + "Error reading threads.txt: " + str(e) + RESET)
    return config

def load_spreadsheet_id():
    filename = "spreadsheet_id.txt"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return f.read().strip()  # File harus berisi hanya Spreadsheet ID
    else:
        return input(GREEN + "File spreadsheet_id.txt tidak ditemukan! Masukkan Spreadsheet ID: " + RESET).strip()

########################################
# FUNGSI UNTUK MENAMPILKAN LOGO
########################################

def tampilkan_logo():
    width = 80  # Lebar tampilan yang diinginkan
    logo = dedent(f"""{WHITE}
██████  ██████   ██████  ██████  ██   ██      ██ ██    ██ ███    ██  ██████  ██      ███████ ██████      
██   ██ ██   ██ ██    ██ ██   ██  ██ ██       ██ ██    ██ ████   ██ ██       ██      ██      ██   ██     
██   ██ ██████  ██    ██ ██████    ███        ██ ██    ██ ██ ██  ██ ██   ███ ██      █████   ██████      
██   ██ ██   ██ ██    ██ ██       ██ ██  ██   ██ ██    ██ ██  ██ ██ ██    ██ ██      ██      ██   ██     
██████  ██   ██  ██████  ██      ██   ██  █████   ██████  ██   ████  ██████  ███████ ███████ ██   ██     
                                                                                                         
                                         ANALYSIS TOOLS                                                                
{RESET}\n""")
    print(logo)

########################################
# GOOGLE SHEETS API FUNCTION
########################################

def build_sheets_service():
   # Inisialisasi Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Dapatkan direktori script saat ini (misal: DROPXJUNGLER/analisa)
script_dir = os.path.dirname(os.path.realpath(_file_))

# Dapatkan direktori induk, yaitu folder DROPXJUNGLER
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

# Susun path lengkap ke file credentials.json di folder induk
credentials_path = os.path.join(parent_dir, 'credentials.json')

# Muat kredensial dari file di folder induk
creds = service_account.Credentials.from_service_account_file(
    credentials_path, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=creds)

def send_to_sheets(record, sheet_name):
    """
    Mengirim record (list dengan 9 elemen) ke Google Sheets.
    Header: Timestamp, Nama Proyek, Jenis Airdrop, Total Persentase,
            Rating Proyek, Prediksi Token, Prediksi Harga Token, Total Reward, Feedback
    Data baru ditulis ke baris genap (misalnya A2:I2, A4:I4, dst.)
    Marker "M" akan ditambahkan di kolom Y pada baris yang sama.
    """
    spreadsheet_id = load_spreadsheet_id()
   # Inisialisasi Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Dapatkan direktori script saat ini (misal: DROPXJUNGLER/reshareshing)
script_dir = os.path.dirname(os.path.realpath(_file_))

# Dapatkan direktori induk, yaitu folder DROPXJUNGLER
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

# Susun path lengkap ke file credentials.json di folder induk
credentials_path = os.path.join(parent_dir, 'credentials.json')

# Muat kredensial dari file di folder induk
creds = service_account.Credentials.from_service_account_file(
    credentials_path, scopes=SCOPES)
sheets_service = build('sheets', 'v4', credentials=creds)

    header = [
        "Timestamp",
        "Nama Proyek",
        "Jenis Airdrop",
        "Total Persentase",
        "Rating Proyek",
        "Prediksi Token",
        "Prediksi Harga Token",
        "Total Reward",
        "Feedback"
    ]
    
    header_range = f"{sheet_name}!A1:I1"
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=header_range).execute()
    values = result.get("values", [])
    if not values or values[0] != header:
        body = {"values": [header]}
        sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=header_range,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        print(GREEN + "Header berhasil ditulis di A1:I1." + RESET)
        data_count = 0
    else:
        data_range = f"{sheet_name}!A2:A"
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=data_range).execute()
        values = result.get("values", [])
        data_count = len([row for row in values if row and row[0].strip() != ""])
    
    next_data_row = 2 * (data_count + 1)
    update_range = f"{sheet_name}!A{next_data_row}:I{next_data_row}"
    body_data = {"values": [record]}
    sheet.values().update(
        spreadsheetId=spreadsheet_id,
        range=update_range,
        valueInputOption="USER_ENTERED",
        body=body_data
    ).execute()
    print(GREEN + f"Data berhasil ditulis di {update_range}." + RESET)
    
    marker_range = f"{sheet_name}!Y{next_data_row}:Y{next_data_row}"
    body_marker = {"values": [["M"]]}
    sheet.values().update(
        spreadsheetId=spreadsheet_id,
        range=marker_range,
        valueInputOption="USER_ENTERED",
        body=body_marker
    ).execute()
    print(GREEN + f"Marker 'M' berhasil ditambahkan di {marker_range}" + RESET)

########################################
# TELEGRAM FUNCTION
########################################

def kirim_ke_telegram(summary, token, chat_id, thread_ids=None):
    if not token or not chat_id:
        print(GREEN + "Token atau Chat ID tidak ditemukan. Periksa file token.txt dan idchat.txt." + RESET)
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": summary,
        "parse_mode": "HTML"
    }
    if thread_ids:
        for thread_id in thread_ids:
            payload["message_thread_id"] = int(thread_id)
            try:
                response = requests.post(url, json=payload)
                if response.ok:
                    print(GREEN + f"Pesan berhasil dikirim ke Telegram untuk thread_id {thread_id}." + RESET)
                else:
                    print(GREEN + f"Gagal mengirim pesan untuk thread_id {thread_id}. Status: {response.status_code}" + RESET)
            except Exception as e:
                print(GREEN + "Error saat mengirim pesan ke Telegram: " + str(e) + RESET)
    else:
        try:
            response = requests.post(url, json=payload)
            if response.ok:
                print(GREEN + "Pesan berhasil dikirim ke Telegram." + RESET)
            else:
                print(GREEN + "Gagal mengirim pesan ke Telegram. Status: " + str(response.status_code) + RESET)
        except Exception as e:
            print(GREEN + "Error saat mengirim pesan ke Telegram: " + str(e) + RESET)

########################################
# FUNGSI EVALUASI & PREDIKSI (MAIN)
########################################

def part1():
    total_score = 0
    proyek = input(GREEN + "\nMasukkan nama proyek airdrop: " + RESET)
    
    situs = input(GREEN + "\nApakah situs berkualitas? (Y/N): " + RESET).strip().upper()
    if situs == "Y":
        opsi_situs = input(GREEN + "Pilih opsi:\n  1. Good (3 poin)\n  2. Biasa aja (2 poin)\nJawaban: " + RESET).strip()
        situs_score = 3 if opsi_situs == "1" else (2 if opsi_situs == "2" else 0)
    else:
        situs_score = 0
    total_score += situs_score

    roadmap = input(GREEN + "\nApakah roadmap berkualitas? (Y/N): " + RESET).strip().upper()
    roadmap_score = 2 if roadmap == "Y" else 1
    total_score += roadmap_score

    whitepaper = input(GREEN + "\nApakah whitepaper berkualitas? (Y/N): " + RESET).strip().upper()
    if whitepaper == "Y":
        opsi_whitepaper = input(GREEN + "Pilih opsi:\n  1. Good (3 poin)\n  2. Biasa (1 poin)\nJawaban: " + RESET).strip()
        whitepaper_score = 3 if opsi_whitepaper == "1" else (1 if opsi_whitepaper == "2" else 0)
    else:
        whitepaper_score = 0
    total_score += whitepaper_score

    faucet = input(GREEN + "\nApakah claim faucet membutuhkan saldo mainnet? (Y/N): " + RESET).strip().upper()
    if faucet == "Y":
        opsi_faucet = input(GREEN + "Pilih opsi:\n  1. Gitcoinpassport (2 poin)\n  2. ETH (2 poin)\n  3. BNB (2 poin)\n  0. Custom (3 poin)\nJawaban: " + RESET).strip()
        faucet_score = 2 if opsi_faucet in ["1", "2", "3"] else (3 if opsi_faucet == "0" else 0)
    else:
        faucet_score = 0
    total_score += faucet_score

    try:
        funding = float(input(GREEN + "\nMasukkan besar funding proyek (dalam USD): " + RESET))
    except:
        funding = 0
    if funding <= 5e6:
        funding_score = 1
    elif funding < 10e6:
        funding_score = 1
    elif funding < 80e6:
        funding_score = 2
    else:
        funding_score = 5
    total_score += funding_score

    block_explorer = input(GREEN + "\nApakah block explorer berkualitas? (Y/N): " + RESET).strip().upper()
    be_score = 2 if block_explorer == "Y" else 0
    total_score += be_score

    tim = input(GREEN + "\nApakah tim berkualitas? (Y/N): " + RESET).strip().upper()
    if tim == "Y":
        opsi_tim = input(GREEN + "Pilih opsi:\n  1. Biasa (1 poin)\n  2. Sedang (2 poin)\n  3. Good (3 poin)\nJawaban: " + RESET).strip()
        tim_score = 1 if opsi_tim == "1" else (2 if opsi_tim == "2" else (3 if opsi_tim == "3" else 0))
    else:
        tim_score = 0
    total_score += tim_score

    twitter = input(GREEN + "\nApakah Twitter berkualitas? (Y/N): " + RESET).strip().upper()
    if twitter == "Y":
        opsi_twitter = input(GREEN + "Pilih opsi:\n  1. Centang kuning (2 poin)\n  2. Centang biru (1 poin)\nJawaban: " + RESET).strip()
        twitter_score = 2 if opsi_twitter == "1" else (1 if opsi_twitter == "2" else 0)
    else:
        twitter_score = 0
    total_score += twitter_score

    telegram_input = input(GREEN + "\nApakah Telegram berkualitas? (Y/N): " + RESET).strip().upper()
    telegram_score = 1 if telegram_input == "Y" else 0
    total_score += telegram_score

    discord = input(GREEN + "\nApakah Discord berkualitas? (Y/N): " + RESET).strip().upper()
    if discord == "Y":
        try:
            members = int(input(GREEN + "Masukkan jumlah anggota Discord: " + RESET))
        except:
            members = 0
        discord_score = 1 if members > 500000 else 5
    else:
        discord_score = 0
    total_score += discord_score

    github = input(GREEN + "\nApakah Github berkualitas? (Y/N): " + RESET).strip().upper()
    github_score = 2 if github == "Y" else 1
    total_score += github_score

    dokumentasi = input(GREEN + "\nApakah dokumentasi berkualitas? (Y/N): " + RESET).strip().upper()
    dokumentasi_score = 2 if dokumentasi == "Y" else 1
    total_score += dokumentasi_score

    backer = input(GREEN + "\nApakah backer terkenal? (Y/N): " + RESET).strip().upper()
    if backer == "Y":
        _ = input(GREEN + "Masukkan nama backer: " + RESET)
        opsi_backer = input(GREEN + "Pilih opsi:\n  1. Biasa (3 poin)\n  2. Terkenal (6 poin)\nJawaban: " + RESET).strip()
        backer_score = 3 if opsi_backer == "1" else (6 if opsi_backer == "2" else 0)
    else:
        backer_score = 1
    total_score += backer_score

    _ = input(GREEN + "\nApakah proyek memiliki sistem anti sybil? (Y/N): " + RESET).strip().upper()
    anti_sybil_score = 0
    total_score += anti_sybil_score

    print(GREEN + "\nPilih jenis airdrop:" + RESET)
    print(GREEN + "  1. Testnet (6 poin)" + RESET)
    print(GREEN + "  2. Web3 (3 poin)" + RESET)
    print(GREEN + "  3. Extension (4 poin)" + RESET)
    print(GREEN + "  4. Aplikasi (4 poin)" + RESET)
    print(GREEN + "  5. Node Testnet (5 poin)" + RESET)
    print(GREEN + "  6. Role Discord (5 poin)" + RESET)
    opsi_airdrop = input(GREEN + "Masukkan opsi (1/2/3/4/5/6): " + RESET).strip()
    if opsi_airdrop == "1":
        airdrop_score = 6
        jenis_airdrop = "Testnet"
    elif opsi_airdrop == "2":
        airdrop_score = 3
        jenis_airdrop = "Web3"
    elif opsi_airdrop == "3":
        airdrop_score = 4
        jenis_airdrop = "Extension"
    elif opsi_airdrop == "4":
        airdrop_score = 4
        jenis_airdrop = "Aplikasi"
    elif opsi_airdrop == "5":
        airdrop_score = 5
        jenis_airdrop = "Node Testnet"
    elif opsi_airdrop == "6":
        airdrop_score = 5
        jenis_airdrop = "Role Discord"
    else:
        airdrop_score = 0
        jenis_airdrop = "Tidak valid"
    total_score += airdrop_score

    max_score = 44
    total_persen = (total_score / max_score) * 100
    if total_persen < 70:
        rating = "Biasa"
    elif total_persen < 80:
        rating = "Potensi"
    else:
        rating = "Sangat Berpotensi"

    print("\n" + GREEN + "--- Hasil Evaluasi Proyek ---" + RESET)
    print(GREEN + f"Nama Proyek   : {proyek}" + RESET)
    print(GREEN + f"Jenis Airdrop : {jenis_airdrop}" + RESET)
    return proyek, jenis_airdrop, total_persen, rating

def prediksi_reward():
    print("\n" + GREEN + "--- Prediksi Reward ---" + RESET)
    print(GREEN + "Pilih opsi prediksi reward:" + RESET)
    print(GREEN + "  1. Rumus Pro Rata (A)" + RESET)
    print(GREEN + "  2. Rumus Piecewise Function (B)" + RESET)
    print(GREEN + "  3. Coming Soon" + RESET)
    pilihan = input(GREEN + "Masukkan opsi (1/2/3): " + RESET).strip()

    reward_output = ""
    token_value = 0

    if pilihan == "1":
        print("\n" + GREEN + "-- Rumus Pro Rata (A) --" + RESET)
        _ = input(GREEN + "Pilih sistem (Point/Badge): " + RESET).strip().lower()
        tahu_total = input(GREEN + "Apakah Anda tahu total poin airdrop? (Y/N): " + RESET).strip().upper()
        if tahu_total == "Y":
            try:
                total_poin_airdrop = float(input(GREEN + "Masukkan total poin airdrop: " + RESET))
                poin_individu = float(input(GREEN + "Masukkan poin individu: " + RESET))
                total_supply = float(input(GREEN + "Masukkan total supply: " + RESET))
                allocation_airdrop = float(input(GREEN + "Masukkan alokasi airdrop (misal 0.1 untuk 10%): " + RESET))
            except Exception as e:
                print(GREEN + "Input tidak valid, menggunakan nilai 0 untuk semua variabel." + RESET)
                total_poin_airdrop = poin_individu = total_supply = allocation_airdrop = 0
            if total_poin_airdrop > 0:
                token_value = (poin_individu / total_poin_airdrop) * (total_supply * allocation_airdrop)
            else:
                token_value = 0
            reward_output = f"Token yang Diterima: {token_value}"
        else:
            prediksi = input(GREEN + "Apakah Anda memiliki prediksi? (Y/N): " + RESET).strip().upper()
            if prediksi == "Y":
                try:
                    prediksi_poin = float(input(GREEN + "Masukkan prediksi poin airdrop: " + RESET))
                    total_prediksi_poin = float(input(GREEN + "Masukkan prediksi total poin airdrop: " + RESET))
                except:
                    prediksi_poin = total_prediksi_poin = 0
                if total_prediksi_poin > 0:
                    token_value = (prediksi_poin / total_prediksi_poin) * 100
                else:
                    token_value = 0
                reward_output = f"Prediksi Token yang Diterima (perkiraan): {token_value}"
            else:
                reward_output = "Data reward tidak tersedia, silakan input prediksi."
    elif pilihan == "2":
        print("\n" + GREEN + "-- Rumus Piecewise Function (B) --" + RESET)
        try:
            B = float(input(GREEN + "Masukkan jumlah badge: " + RESET))
        except:
            B = 0
        if B < 10:
            token_value = 0
        elif B < 15:
            token_value = 60
        elif B < 20:
            token_value = 100
        elif B < 200:
            token_value = 150
        else:
            token_value = 250
        reward_output = f"Jumlah token (prediksi): {token_value}"
    elif pilihan == "3":
        reward_output = "Fitur prediksi reward akan segera hadir."
    else:
        reward_output = "Opsi tidak valid."

    print(GREEN + reward_output + RESET)
    return reward_output, token_value

def prediksi_harga():
    print("\n" + GREEN + "--- Prediksi Harga Token ---" + RESET)
    while True:
        try:
            total_supply = float(input(GREEN + "Masukkan total supply: " + RESET))
            break
        except:
            print(GREEN + "Input tidak valid untuk total supply. Silakan masukkan angka." + RESET)

    manual_choice = input(GREEN + "Apakah Anda ingin memasukkan market cap secara manual? (Y/N): " + RESET).strip().upper()
    if manual_choice == "Y":
        try:
            market_cap_proj = float(input(GREEN + "Masukkan market cap yang diproyeksikan (USD): " + RESET))
        except:
            print(GREEN + "Input tidak valid, menggunakan default market cap = 0." + RESET)
            market_cap_proj = 0
    elif manual_choice == "N":
        print(GREEN + "Pilih opsi market cap yang diprediksi:" + RESET)
        print(GREEN + "  1. $100,000,000" + RESET)
        print(GREEN + "  2. $200,000,000" + RESET)
        print(GREEN + "  3. $500,000,000" + RESET)
        print(GREEN + "  4. $1,000,000,000" + RESET)
        opsi = input(GREEN + "Masukkan opsi (1/2/3/4): " + RESET).strip()
        if opsi == "1":
            market_cap_proj = 100_000_000
        elif opsi == "2":
            market_cap_proj = 200_000_000
        elif opsi == "3":
            market_cap_proj = 500_000_000
        elif opsi == "4":
            market_cap_proj = 1_000_000_000
        else:
            print(GREEN + "Opsi tidak valid, menggunakan default market cap = 0." + RESET)
            market_cap_proj = 0
    else:
        print(GREEN + "Pilihan tidak valid, menggunakan default market cap = 0." + RESET)
        market_cap_proj = 0

    predicted_price = market_cap_proj / total_supply if total_supply else 0
    print(GREEN + f"Harga Token Diprediksi: ${predicted_price:,.6f}" + RESET)
    return predicted_price

def confirmed_feedback():
    while True:
        print("\n" + GREEN + "--- Feedback ---" + RESET)
        fb = input(GREEN + "Silakan berikan feedback Anda tentang evaluasi ini: " + RESET)
        yakin = input(GREEN + "Apakah Anda yakin dengan feedback ini? (Y/N): " + RESET).strip().upper()
        if yakin == "Y":
            print(GREEN + "Feedback dikonfirmasi. Terima kasih!" + RESET)
            return fb
        else:
            print(GREEN + "Silakan ulangi feedback Anda." + RESET)

########################################
# FUNCTION: PRINT SUMMARY (TANPA GARIS)
########################################

def print_summary(lines):
    if not lines:
        return
    for line in lines:
        print(line)

########################################
# MAIN FUNCTION
########################################

def main():
    # Tampilkan logo di awal program (logo putih)
    tampilkan_logo()
    
    print("\n" + GREEN + "="*40 + RESET)
    # Tidak menampilkan header tambahan
    
    proyek, jenis_airdrop, total_persen, rating = part1()
    reward, token_value = prediksi_reward()
    predicted_price = prediksi_harga()
    total_reward = token_value * predicted_price
    user_feedback = confirmed_feedback()

    # Format timestamp: jam:menit:detik tanggal/bulan/tahun
    timestamp = datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    record = [
        timestamp,
        proyek,
        jenis_airdrop,
        f"{total_persen:.0f}%",
        rating,
        token_value,
        f"${predicted_price:,.6f}",
        f"${total_reward:,.2f}",
        user_feedback
    ]

    summary_lines = [
        f"Nama Proyek   : {proyek}",
        f"Jenis Airdrop : {jenis_airdrop}",
        f"Total Persen  : {total_persen:.0f}%",
        f"Rating Proyek : {rating}",
        f"Prediksi Token: {token_value}",
        f"Prediksi Harga: ${predicted_price:,.6f}",
        f"Total Reward  : ${total_reward:,.2f}"
    ]
    print_summary(summary_lines)

    config = load_config()
    summary_text = "\n".join(summary_lines)
    if config["thread_ids"]:
        kirim_ke_telegram(summary_text, config["token"], config["chat_id"], config["thread_ids"])
    else:
        kirim_ke_telegram(summary_text, config["token"], config["chat_id"])

    send_to_sheets(record, "analysis")
    print(GREEN + "\n✅ Data berhasil dikirim!" + RESET)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{GREEN}Program dihentikan oleh pengguna.{RESET}")
