import re
import requests
import shutil
import time
import math
import threading
import os  # Tambahkan import os
from sys import stdout, stderr
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Variabel status global
gsheet_status = "Google Sheets: Pending"
telegram_status = "Telegram: Pending"
gsheet_link = None

# Kode warna ANSI
reset = "\033[0m"
alternate_screen = "\033[?1049h"
main_screen = "\033[?1049l"

def hsv_to_rgb(h, s, v):
    h = h % 1.0
    i = int(h * 6)
    f = h * 6 - i
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    if i == 0:
        return (v, t, p)
    if i == 1:
        return (q, v, p)
    if i == 2:
        return (p, v, t)
    if i == 3:
        return (p, q, v)
    if i == 4:
        return (t, p, v)
    return (v, p, q)

def rainbow_color(progress):
    hue = progress % 1.0
    r, g, b = hsv_to_rgb(hue, 0.8, 1.0)
    return f"\033[38;2;{int(r*255)};{int(g*255)};{int(b*255)}m"

def text_shimmer_color(progress, char_index):
    hue = (progress + char_index * 0.02) % 1.0
    r, g, b = hsv_to_rgb(hue, 0.8, 0.8)
    return f"\033[38;2;{int(r*255)};{int(g*255)};{int(b*255)}m"

ascii_art = r"""
██████╗ ██╗  ██╗     ██╗
██╔══██╗╚██╗██╔╝     ██║
██║  ██║ ╚███╔╝      ██║
██║  ██║ ██╔██╗ ██   ██║
██████╔╝██╔╝ ██╗╚█████╔╝
╚═════╝ ╚═╝  ╚═╝ ╚════╝ 
       DROPXJUNGLER
"""

def scale_ascii_art(art, max_width):
    lines = [line.rstrip() for line in art.splitlines() if line.strip()]
    if not lines:
        return []
    original_width = max(len(line) for line in lines)
    scale_factor = min(1.0, (max_width - 4) / original_width)
    new_width = int(original_width * scale_factor)
    new_height = int(len(lines) * scale_factor)
    scaled = []
    for y in range(new_height):
        src_y = int(y / scale_factor)
        line = lines[src_y]
        scaled_line = ""
        for x in range(new_width):
            src_x = int(x / scale_factor)
            scaled_line += line[src_x] if src_x < len(line) else " "
        scaled.append(scaled_line)
    return scaled

def animate():
    stdout.write(alternate_screen)
    stdout.write("\033[?25l")
    try:
        term_width, term_height = shutil.get_terminal_size()
        art_lines = scale_ascii_art(ascii_art, term_width - 4)
        art_height = len(art_lines)
        # Kita butuh 5 baris info: 1 baris DATACURATOR (underlined), 1 baris info, 2 baris status, 1 baris terimakasih.
        v_pad = max(0, (term_height - art_height - 5) // 2)
        
        # Gambar border statis
        border = "═" * (term_width - 2)
        top_border = f"\033[0;0H\033[37m╔{border}╗"
        bottom_border = f"\033[{term_height};0H\033[37m╚{border}╝"
        stdout.write(top_border + bottom_border)
        
        start_time = time.time()
        while True:
            progress = (time.time() - start_time) * 0.3
            buffer = []
            # Render ASCII art dengan efek shimmer
            for i, line in enumerate(art_lines):
                line_buffer = []
                for j, char in enumerate(line):
                    color = text_shimmer_color(progress, i + j)
                    line_buffer.append(f"{color}{char}")
                row = i + v_pad + 1
                h_pad_line = max(0, (term_width - len(line)) // 2)
                buffer.append(f"\033[{row};{h_pad_line + 1}H{''.join(line_buffer)}")
            
            # Info di bawah art
            info_y = v_pad + art_height + 2
            
            datacurator_text = "DATACURATOR"
            datacurator_underlined = "\033[4m" + datacurator_text + "\033[24m"
            dc_x = (term_width - len(datacurator_text)) // 2 + 1
            
            info_text = "Aggregating Data | Google Sheets & Telegram Integration"
            info_x = (term_width - len(info_text)) // 2 + 1
            
            status_gsheet_text = gsheet_status
            status_gsheet_x = (term_width - len(status_gsheet_text)) // 2 + 1
            
            status_tg_text = telegram_status
            status_tg_x = (term_width - len(status_tg_text)) // 2 + 1
            
            thanks_text = "terimakasih♥"
            thanks_x = (term_width - len(thanks_text)) // 2 + 1
            
            buffer.append(f"\033[{info_y};{dc_x}H{datacurator_underlined}")
            buffer.append(f"\033[{info_y+1};{info_x}H{info_text}")
            buffer.append(f"\033[{info_y+2};{status_gsheet_x}H{status_gsheet_text}")
            buffer.append(f"\033[{info_y+3};{status_tg_x}H{status_tg_text}")
            buffer.append(f"\033[{info_y+4};{thanks_x}H{thanks_text}")
            
            # Gambar ulang side borders dengan efek warna pelangi
            border_color = rainbow_color(progress)
            for r in range(1, term_height + 1):
                buffer.append(f"{border_color}\033[{r};1H║")
                buffer.append(f"{border_color}\033[{r};{term_width}H║")
            
            stdout.write(''.join(buffer))
            stdout.flush()
            time.sleep(0.08)
    except KeyboardInterrupt:
        pass
    finally:
        stdout.write(main_screen)
        stdout.write("\033[?25h")

def read_config_value(filename):
    with open(filename, 'r') as f:
        return f.read().strip()

# Baca konfigurasi Telegram dari file
TELEGRAM_BOT_TOKEN = read_config_value('token.txt')
TELEGRAM_CHAT_ID = read_config_value('idchat.txt')
try:
    THREADS_ID = int(read_config_value('threads.txt'))
except ValueError:
    THREADS_ID = None

def update_google_sheet():
    global gsheet_status, gsheet_link
    try:
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        script_dir = os.path.dirname(os.path.realpath(__file__))

        parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))

        credentials_path = os.path.join(parent_dir, 'credentials.json')

        creds = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES)
        sheets_service = build('sheets', 'v4', credentials=creds)
    
        def read_source_ids(filename):
            source_ids = []
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        source_ids.append(parts[1].strip())
            return source_ids
        
        def remove_columns_yz(row):
            return [cell for idx, cell in enumerate(row) if idx not in (24, 25)]
        
        source_spreadsheet_ids = read_source_ids('copyid.txt')

        destination_spreadsheet_id = read_config_value('datacuratorid.txt')
        destination_sheet_name = "Datacurator"
        
        header_range = f"{destination_sheet_name}!A1:{chr(64+20)}1"
        try:
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=destination_spreadsheet_id,
                range=header_range
            ).execute()
            existing_header = result.get('values', [])
        except Exception as e:
            existing_header = []
        if not existing_header:
            first_src_id = source_spreadsheet_ids[0]
            metadata = sheets_service.spreadsheets().get(spreadsheetId=first_src_id).execute()
            first_sheet_title = metadata['sheets'][0]['properties']['title']
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=first_src_id,
                range=f"{first_sheet_title}!1:1"
            ).execute()
            header = result.get('values', [[]])[0]
            if not header:
                header = ["Kolom1", "Kolom2", "Kolom3"]
            body = {'values': [header]}
            sheets_service.spreadsheets().values().update(
                spreadsheetId=destination_spreadsheet_id,
                range=f"{destination_sheet_name}!A1:{chr(64+len(header))}1",
                valueInputOption="RAW",
                body=body
            ).execute()
        
        all_data = []

        for src_id in source_spreadsheet_ids:
            try:
                metadata = sheets_service.spreadsheets().get(spreadsheetId=src_id).execute()
                sheet_title = metadata['sheets'][0]['properties']['title']
                src_range = f"{sheet_title}"
                result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=src_id,
                    range=src_range
                ).execute()
                values = result.get('values', [])
                if not values or len(values) < 2:
                    continue
                data_rows = values[1:]
                for row in data_rows:
                    processed_row = remove_columns_yz(row)
                    all_data.append(processed_row)
                for _ in range(3):
                    all_data.append([])
            except Exception as e:
                continue
        
        dest_range = f"{destination_sheet_name}!A2"
        body = {'values': all_data}
        sheets_service.spreadsheets().values().append(
            spreadsheetId=destination_spreadsheet_id,
            range=dest_range,
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        
        result_rows = sheets_service.spreadsheets().values().get(
            spreadsheetId=destination_spreadsheet_id,
            range=f"{destination_sheet_name}!A:A"
        ).execute()
        total_rows = len(result_rows.get('values', []))
        
        result_ay = sheets_service.spreadsheets().values().get(
            spreadsheetId=destination_spreadsheet_id,
            range=f"{destination_sheet_name}!AY2:AY{total_rows}"
        ).execute()
        ay_values = result_ay.get('values', [])
        
        even_row_to_update = None
        for i in range(2, total_rows+1):
            if i % 2 == 0:
                if i-2 < len(ay_values):
                    cell_val = ay_values[i-2]
                    if not cell_val atau not cell_val[0].strip():
                        even_row_to_update = i
                        break
                else:
                    even_row_to_update = i
                    break
        if even_row_to_update is None:
            next_even = total_rows + 1 if (total_rows + 1) % 2 == 0 else total_rows + 2
            even_row_to_update = next_even
        
        ay_range = f"{destination_sheet_name}!AY{even_row_to_update}"
        body = {'values': [["M"]]}
        sheets_service.spreadsheets().values().update(
            spreadsheetId=destination_spreadsheet_id,
            range=ay_range,
            valueInputOption="RAW",
            body=body
        ).execute()
        
        gsheet_link = f"https://docs.google.com/spreadsheets/d/{destination_spreadsheet_id}/edit#gid=0"
        gsheet_status = "Google Sheets: Success"
    except Exception as e:
        gsheet_status = f"Google Sheets: Failed ({e})"

def send_telegram_message():
    global telegram_status, gsheet_link
    while gsheet_link is None:
        time.sleep(0.5)
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        message = f"Link Google Sheet: {gsheet_link}"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
        }
        if THREADS_ID is not None:
            payload["message_thread_id"] = THREADS_ID
        response = requests.post(url, data=payload)
        response.raise_for_status()
        telegram_status = "Telegram: Success"
    except Exception as e:
        telegram_status = f"Telegram: Failed ({e})"

if __name__ == "__main__":
    thread_gs = threading.Thread(target=update_google_sheet)
    thread_tg = threading.Thread(target=send_telegram_message)
    thread_gs.start()
    thread_tg.start()
    
    animate()
