# -*- coding: utf-8 -*-
import os
import datetime
import requests
import json
from textwrap import dedent
from google.oauth2 import service_account
from googleapiclient.discovery import build
import google.generativeai as genai
import traceback # Untuk error handling detail
import re # Untuk menghapus tag HTML

# --- KONFIGURASI WARNA TERMINAL ---
GREEN = "\033[92m"
WHITE = "\033[97m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

# --- FUNGSI TAMPILKAN LOGO ---
def tampilkan_logo():
    """Menampilkan logo ASCII Art DROPXJUNGLER (Original)."""
    logo = dedent(f"""{BOLD}{WHITE}
████████████ █████████████   ██   ███    ████    ██████████    ████████████     
██   ███   ███    ███   ███ ██    ███    █████   ███     ██    ██    ██   ██    
██   █████████    ███████ ███     ███    ███ ██  ███   ████    █████ ██████     
██   ███   ███    ███    ██ ███   ███    ███  ██ ███    ███    ██    ██   ██    
████████   ██████████   ██   ██████ ████████   ████████████████████████   ██    
                                                                                                                                                                
{RESET}
{CYAN}{BOLD}{" " * 28}ANALYSIS TOOLS V2.3{RESET}
{CYAN}{"-"*70}{RESET}""")
    print(logo)

# --- KONFIGURASI & UTILITAS ---

def load_configuration_files():
    """Memuat semua file konfigurasi dengan pesan ringkas."""
    print(CYAN + BOLD + "\n--- Memuat Konfigurasi ---" + RESET)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir))
    search_dirs = [script_dir, parent_dir]
    config_data = {"ai_api_key":None,"telegram_token":None,"telegram_chat_id":None,"telegram_thread_ids":[],"spreadsheet_id":None,"google_credentials_path":None,"ai_model":None,"sheets_service":None}
    files_to_check = {"ai_api_key":"api_key.txt","telegram_token":"token.txt","telegram_chat_id":"idchat.txt","telegram_thread_ids":"threads.txt","spreadsheet_id":"spreadsheet_id.txt","google_credentials_path":"credentials.json"}

    for key, filename in files_to_check.items():
        found_path=None; content=None; error_msg=None
        for directory in search_dirs:
            filepath=os.path.join(directory, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r") as f:
                        if key=="telegram_thread_ids": content=[ln.strip() for ln in f if ln.strip()]
                        elif key=="google_credentials_path": content=filepath
                        else: content=f.read().strip()
                    if content or key in ["telegram_thread_ids", "google_credentials_path"]: found_path=filepath; break
                    else: error_msg=f"{YELLOW}[!] File '{filename}' kosong.{RESET}"
                except Exception as e: error_msg=f"{RED}[X] Error baca '{filename}': {e}{RESET}"
        if found_path:
             if key=="google_credentials_path": config_data[key]=content; print(f"{GREEN}[OK] Ditemukan:{RESET} '{filename}'")
             elif content or key=="telegram_thread_ids":
                 config_data[key]=content; status=f"({len(content)} IDs)" if key=="telegram_thread_ids" else ""; print(f"{GREEN}[OK] Dimuat:  {RESET} '{filename}' {status}")
             elif error_msg: print(error_msg)
        elif error_msg: print(error_msg)
        else:
            is_optional=key in ["telegram_thread_ids"]; color=CYAN if is_optional else YELLOW; status="[Info]" if is_optional else "[!]"
            print(f"{color}{status} Opsional:{RESET} '{filename}' T/A." if is_optional else f"{color}{status} Warning:{RESET} '{filename}' T/A.")

    if config_data["ai_api_key"]:
        try:
            genai.configure(api_key=config_data["ai_api_key"]); model=genai.GenerativeModel('gemini-1.5-flash'); model.generate_content("Test",generation_config=genai.types.GenerationConfig(max_output_tokens=5))
            config_data["ai_model"]=model; print(f"{GREEN}[OK] Service:{RESET} AI Gemini OK.")
        except Exception as e: print(RED+f"[X] Service:{RESET} Gagal AI: {e}"); config_data["ai_model"]=None
    else:
        env_key=os.environ.get("GOOGLE_API_KEY")
        if env_key:
             print(f"{CYAN}[Info] Mencoba API Key AI dari ENV...{RESET}")
             try:
                 genai.configure(api_key=env_key); model=genai.GenerativeModel('gemini-1.5-flash'); model.generate_content("Test",generation_config=genai.types.GenerationConfig(max_output_tokens=5))
                 config_data["ai_model"]=model; print(f"{GREEN}[OK] Service:{RESET} AI OK (via ENV).")
             except Exception as e: print(RED+f"[X] Service:{RESET} Gagal AI (via ENV): {e}")
        else: print(f"{YELLOW}[!] Service:{RESET} AI nonaktif (API Key T/A).")

    if config_data["google_credentials_path"]:
        try:
            SCOPES=['https://www.googleapis.com/auth/spreadsheets']; creds=service_account.Credentials.from_service_account_file(config_data["google_credentials_path"], scopes=SCOPES)
            sheets_service=build('sheets','v4',credentials=creds); config_data["sheets_service"]=sheets_service; print(f"{GREEN}[OK] Service:{RESET} GSheets OK.")
        except Exception as e: print(RED+f"[X] Service:{RESET} Gagal GSheets: {e}"); config_data["sheets_service"]=None
    else: print(f"{YELLOW}[!] Service:{RESET} GSheets nonaktif (credentials.json T/A).")

    if not config_data["spreadsheet_id"]:
        print(f"{YELLOW}[!] Info:{RESET} 'spreadsheet_id.txt' T/A.")
        while True:
            ssid_input=input(GREEN+"   -> Masukkan Spreadsheet ID: "+RESET).strip()
            if ssid_input: config_data["spreadsheet_id"]=ssid_input; break
            else: print(RED+"[X] ID kosong."+RESET)
    print(CYAN+"---------------------------"+RESET)
    return config_data

# --- Fungsi Google Sheets ---
def send_to_sheets(record, sheet_name, config):
    sheets_service = config.get("sheets_service"); spreadsheet_id = config.get("spreadsheet_id")
    if not sheets_service or not spreadsheet_id: print(YELLOW+"\n[!] GSheets nonaktif. Skip."+RESET); return
    print(CYAN+f"\n--- Mengirim ke GSheets (Sheet: {sheet_name}) ---"+RESET)
    sheet = sheets_service.spreadsheets()
    header = ["Timestamp","Nama Proyek","Jenis Airdrop","Total Persentase (%)","Rating Proyek","Prediksi Token","Prediksi Harga Token ($)","Total Reward Est ($)","Feedback"]
    header_range = f"{sheet_name}!A1:I1"
    try:
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=header_range).execute(); values = result.get("values", [])
        if not values or values[0] != header:
            sheet.values().update(spreadsheetId=spreadsheet_id, range=header_range, valueInputOption="USER_ENTERED", body={"values":[header]}).execute()
            print(CYAN+"[Info] Header GSheets ditulis."+RESET); data_count=0
        else:
            check_range=f"{sheet_name}!A2:A"; result=sheet.values().get(spreadsheetId=spreadsheet_id, range=check_range).execute()
            data_count=len([row for row in result.get("values", []) if row and row[0].strip()])
        next_data_row=data_count+2; update_range=f"{sheet_name}!A{next_data_row}:I{next_data_row}"
        sheet.values().update(spreadsheetId=spreadsheet_id, range=update_range, valueInputOption="USER_ENTERED", body={"values":[record]}).execute()
        print(GREEN+f"[OK] Data OK -> GSheets (baris {next_data_row})."+RESET)
    except Exception as e: print(RED+f"[X] Error GSheets: {e}"+RESET)

# --- Fungsi Telegram ---
def kirim_ke_telegram(summary, config):
    token=config.get("telegram_token"); chat_id=config.get("telegram_chat_id"); thread_ids=config.get("telegram_thread_ids",[])
    if not token or not chat_id: print(YELLOW+"\n[!] Telegram nonaktif. Skip."+RESET); return
    print(CYAN+"\n--- Mengirim ke Telegram ---"+RESET)
    url=f"https://api.telegram.org/bot{token}/sendMessage"; base_payload={"chat_id":str(chat_id),"text":summary,"parse_mode":"HTML","disable_web_page_preview":True}
    if thread_ids:
        print(CYAN+f"[Info] Ke Threads: {thread_ids}"+RESET)
        for tid in thread_ids:
            tid_str=str(tid).strip()
            if not tid_str.isdigit(): print(YELLOW+f"[!] Skip thread invalid: {tid_str}"+RESET); continue
            payload=base_payload.copy(); payload["message_thread_id"]=int(tid_str)
            try: r=requests.post(url,json=payload,timeout=15); r.raise_for_status(); print(GREEN+f"[OK] -> thread {tid_str}."+RESET)
            except Exception as e: print(RED+f"[X] Gagal thread {tid_str}: {e}"+RESET)
    print(CYAN+f"[Info] Ke Chat utama: {chat_id}"+RESET)
    try: payload=base_payload.copy(); r=requests.post(url,json=payload,timeout=15); r.raise_for_status(); print(GREEN+"[OK] -> chat utama."+RESET)
    except Exception as e: print(RED+f"[X] Gagal chat utama: {e}"+RESET)

# --- Fungsi AI & Konfirmasi Pengguna ---
def get_ai_analysis(model, project_name, project_url=None):
    prompt = f"""
    Analisis proyek airdrop crypto: "{project_name}". URL: {project_url if project_url else 'N/A'}.
    Nilai HANYA kategori ini (Bahasa Indonesia), HANYA opsi dalam kurung:
    1. Kualitas Situs Web: (Good, Biasa, Poor, Tidak Ditemukan)
    2. Kualitas Roadmap: (Good, Biasa, Poor, Tidak Ditemukan)
    3. Kualitas Whitepaper: (Good, Biasa, Poor, Tidak Ditemukan)
    4. Kualitas Tim: (Good [Publik & Exp], Sedang [Publik Kurang Info], Biasa [Info Minim], Anonim/Tidak Diketahui)
    5. Kualitas Twitter: (Verified Kuning [Org], Verified Biru [Legacy], Standard [Aktif], Tidak Aktif/Tidak Ditemukan)
    6. Kualitas Telegram: (Aktif & Profesional, Biasa [Kurang Aktif/Spam], Tidak Aktif/Tidak Ditemukan)
    7. Kualitas Discord: (Sangat Aktif [>500k & Rapi], Aktif [Ramai], Biasa [Sepi], Tidak Aktif/Tidak Ditemukan)
    8. Kualitas Github: (Aktif & Berkualitas, Ada tapi Kurang Aktif, Tidak Ditemukan)
    9. Kualitas Dokumentasi: (Lengkap & Jelas, Ada tapi Kurang, Tidak Ditemukan)
    10. Reputasi Backer/Investor: (Terkenal [Tier 1/2 VC], Biasa [Kurang Dikenal], Tidak Diketahui)
    Format HANYA JSON valid tanpa teks lain. Contoh: {{"Kualitas Situs Web": "Good", ...}}"""
    if not model: print(YELLOW+"\n[!] Model AI nonaktif. Skip AI."+RESET); return None
    print(CYAN+"\nMeminta analisis AI..."+RESET)
    try:
        response = model.generate_content(prompt, request_options={'timeout': 120})
        cleaned_text = response.text.strip(); json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0); ai_results = json.loads(json_str); print(GREEN+"[OK] Analisis AI OK."+RESET)
            required = ["Kualitas Situs Web","Kualitas Roadmap","Kualitas Whitepaper","Kualitas Tim","Kualitas Twitter","Kualitas Telegram","Kualitas Discord","Kualitas Github","Kualitas Dokumentasi","Reputasi Backer/Investor"]
            missing = [k for k in required if k not in ai_results]
            if missing: print(YELLOW+f"[!] AI JSON kurang: {missing}"+RESET); [ai_results.setdefault(k,"Tidak Diketahui") for k in missing]
            return ai_results
        else: print(RED+"[X] AI tidak return JSON."+RESET); return None
    except Exception as e: print(RED+f"[X] Error AI: {e}"+RESET); return None

def confirm_or_override(ai_model, item_name, question_num, question_text, ai_suggestion, options_map):
    """Menampilkan saran AI, meminta konfirmasi/override, dengan opsi analisis link."""
    print(CYAN+f"\n{question_num}. {question_text}"+RESET)
    not_found_keys = {"tidak_ditemukan","poor","anonim_atau_tidak_diketahui","tidak_aktif_atau_tidak_ditemukan","tidak_diketahui"}
    ai_sugg_text = ai_suggestion if ai_suggestion else "Tidak Diketahui"
    norm_sugg = ai_sugg_text.lower().replace(' ','_').replace('&','_and_').replace('>','gt').replace('<','lt').replace('[','').replace(']','').replace('(','').replace(')','').replace('/','_atau_')
    is_not_found = norm_sugg in not_found_keys
    link_analysis_done = False

    if is_not_found and ai_model:
        print(f"{YELLOW}Saran AI: {ai_sugg_text}{RESET}")
        while True:
            ask_link = input(GREEN+f"   Punya link {item_name}? (y/n): "+RESET).strip().lower()
            if ask_link == 'y':
                link_info = input(GREEN+f"   Link {item_name}: "+RESET).strip()
                if link_info:
                    print(CYAN+f"   Menganalisis link..."+RESET)
                    valid_q = [v[0] for k, v in options_map.items() if k.isdigit() and isinstance(v, list) and len(v)>1 and isinstance(v[1], int) and v[1] >= 0]
                    prompt2 = f"Kualitas '{item_name}' dari URL: {link_info}. Jawab HANYA satu dari: {', '.join(valid_q)}. Jika TBD, jawab 'Tidak Bisa Dinilai'."
                    try:
                        resp2 = ai_model.generate_content(prompt2, request_options={'timeout': 90}); assess = resp2.text.strip()
                        print(YELLOW+f"   AI (Link): '{assess}'"+RESET)
                        # --- Perbaikan: Inisialisasi sebelum loop ---
                        selected_score, selected_desc = None, f"AI Link ({assess})"
                        # --- Akhir Perbaikan ---
                        for k, v in options_map.items():
                            # Pastikan v adalah list/tuple dengan 2 elemen sebelum unpacking
                            if isinstance(v, (list, tuple)) and len(v) == 2:
                                opt_desc, opt_score = v # Unpack yg benar
                                if assess.lower() == opt_desc.lower():
                                    selected_score = opt_score
                                    selected_desc = opt_desc+" (AI Link)"
                                    break # Ditemukan, keluar loop
                        if selected_score is not None:
                            print(WHITE+f"   -> Skor link: {selected_desc} ({selected_score})"+RESET)
                            link_analysis_done = True; return selected_score, selected_desc
                        else: print(YELLOW+"   -> Hasil link TBD/tdk cocok. Nilai manual."+RESET); break
                    except Exception as e: print(RED+f"   Gagal AI link: {e}"+RESET); print(YELLOW+"   -> Nilai manual."+RESET); break
                else: print(YELLOW+"Link kosong -> Manual."+RESET); break
            elif ask_link == 'n': print(CYAN+"OK -> Manual."+RESET); break
            else: print(RED+"Jawab y/n."+RESET)

    # --- Logika Utama / Fallback ---
    ai_score_info = None
    if not link_analysis_done:
         ai_score_info = options_map.get(norm_sugg) # Cek saran awal
         score_text = f"({ai_score_info[1]} poin)" if isinstance(ai_score_info, list) and len(ai_score_info) > 1 else "(?)"
         print(f"{YELLOW}Saran AI: {ai_sugg_text} {score_text}{RESET}")

    opts_str = "\n".join([f"  {WHITE}{k}.{RESET} {v[0]} ({v[1]})" for k, v in options_map.items() if k.isdigit() and isinstance(v, list) and len(v)>1])
    prompt_base = GREEN+f"Pilih [{item_name}]:\n{opts_str}"
    prompt_opts = []
    # Hanya tampilkan opsi 'a' jika ai_score_info valid
    if ai_score_info and isinstance(ai_score_info, list) and len(ai_score_info) > 1:
        prompt_opts.append(f"  {WHITE}a.{RESET} Setuju AI ({ai_score_info[0]})")
    prompt_opts.append(f"  {WHITE}x.{RESET} Nilai Manual")
    prompt_text = prompt_base+"\n"+"\n".join(prompt_opts)+"\nJawaban: "+RESET

    while True:
        choice = input(prompt_text).strip().lower()
        # --- PERBAIKAN DISINI ---
        if choice == 'a' and ai_score_info and isinstance(ai_score_info, list) and len(ai_score_info) > 1:
            desc, score = ai_score_info # Unpack: deskripsi dulu, baru skor
            print(WHITE+f"-> Setuju AI: {desc} ({score})"+RESET)
            return score, desc+" (AI)" # Return: skor dulu, baru deskripsi

        elif choice == 'x' or (choice == 'a' and (not ai_score_info or not isinstance(ai_score_info, list) or len(ai_score_info) < 2)):
            if choice=='a': print(YELLOW+"AI awal ? -> Manual."+RESET)
            man_prompt = GREEN+f"   Nilai Manual [{item_name}] (nomor): "+RESET
            while True:
                manual_key = input(man_prompt).strip()
                if manual_key.isdigit() and manual_key in options_map:
                    option_list = options_map[manual_key]
                    if isinstance(option_list, list) and len(option_list) > 1:
                         desc, score = option_list # Unpack
                         print(WHITE+f"-> Manual: {desc} ({score})"+RESET)
                         return score, desc+" (Manual)" # Return
                    else: print(RED+"Format opsi map salah."+RESET) # Error handling internal
                else: print(RED+"Input nomor."+RESET)

        elif choice.isdigit() and choice in options_map:
            option_list = options_map[choice]
            if isinstance(option_list, list) and len(option_list) > 1:
                desc, score = option_list # Unpack
                print(WHITE+f"-> Pilihan: {desc} ({score})"+RESET)
                return score, desc+" (Pilihan Langsung)" # Return
            else: print(RED+"Format opsi map salah."+RESET) # Error handling internal

        else: print(RED+"Input tidak valid."+RESET)
        # --- AKHIR PERBAIKAN ---

# --- FUNGSI EVALUASI UTAMA (PART 1) ---
# (Tidak ada perubahan signifikan di part1, hanya pemanggilan confirm_or_override)
def part1(config):
    ai_model = config.get("ai_model"); evaluation_results = {}; total_score = 0; max_score_possible = 0
    print(CYAN+"\n"+"="*50+RESET); print(CYAN+BOLD+" BAGIAN 1: INFORMASI & EVALUASI PROYEK ".center(50,'=')+RESET); print(CYAN+"="*50+RESET)
    proyek = input(GREEN+"\nNama Proyek: "+RESET).strip()
    while not proyek: print(RED+"Nama kosong."+RESET); proyek=input(GREEN+"Nama Proyek: "+RESET).strip()
    project_url = input(GREEN+"URL Situs Web (opsional): "+RESET).strip()
    evaluation_results["Nama Proyek"]=(0,proyek); evaluation_results["URL Proyek"]=(0, project_url if project_url else "N/A")
    ai_analysis = get_ai_analysis(ai_model, proyek, project_url)
    def get_s(k,d="Tidak Diketahui"): return ai_analysis.get(k,d).strip() if ai_analysis else d
    print(WHITE+BOLD+"\n--- Evaluasi Kriteria ---"+RESET); q_num = 1
    # 1. Situs Web
    opts={"1":["Good",3],"good":["Good",3],"2":["Biasa",2],"biasa":["Biasa",2],"3":["Poor",0],"poor":["Poor",0],"4":["Tdk Ada",0],"tidak_ditemukan":["Tdk Ada",0]}
    max_score_possible+=3; score,desc=confirm_or_override(ai_model,"Situs Web",q_num,"Kualitas Situs Web?",get_s("Kualitas Situs Web"),opts)
    total_score+=score; evaluation_results["Situs Web"]=(score,desc); q_num+=1
    # 2. Roadmap
    opts={"1":["Good",2],"good":["Good",2],"2":["Biasa",1],"biasa":["Biasa",1],"3":["Poor",0],"poor":["Poor",0],"4":["Tdk Ada",0],"tidak_ditemukan":["Tdk Ada",0]}
    max_score_possible+=2; score,desc=confirm_or_override(ai_model,"Roadmap",q_num,"Kualitas Roadmap?",get_s("Kualitas Roadmap"),opts)
    total_score+=score; evaluation_results["Roadmap"]=(score,desc); q_num+=1
    # 3. Whitepaper
    opts={"1":["Good",3],"good":["Good",3],"2":["Biasa",1],"biasa":["Biasa",1],"3":["Poor",0],"poor":["Poor",0],"4":["Tdk Ada",0],"tidak_ditemukan":["Tdk Ada",0]}
    max_score_possible+=3; score,desc=confirm_or_override(ai_model,"Whitepaper",q_num,"Kualitas Whitepaper?",get_s("Kualitas Whitepaper"),opts)
    total_score+=score; evaluation_results["Whitepaper"]=(score,desc); q_num+=1
    # 4. Faucet
    score=0; max_score=3; desc="N/A"; print(CYAN+f"\n{q_num}. Faucet/Modal Awal"+RESET)
    while True:
        f=input(GREEN+"   Perlu saldo mainnet? (y/n): "+RESET).strip().lower()
        if f=='y':
            opts={"1":("Faucet+Syarat",2),"2":("Saldo Mainnet",2),"3":("Khusus/Mahal",3),"0":("Tdk Yakin",1)}
            opts_str="\n".join([f"     {WHITE}{k}.{RESET} {v[0]} ({v[1]})" for k,v in opts.items()]); print(GREEN+"   Pilih jenis:"+RESET+"\n"+opts_str)
            while True:
                o=input(GREEN+"   Pilihan (0-3): "+RESET).strip()
                if o in opts: desc, score = opts[o]; print(WHITE+f"-> Modal: {desc} ({score})"+RESET); break
                else: print(RED+"Input 0-3."+RESET)
            break
        elif f=='n': score=1; desc="Tdk Perlu Modal"; print(WHITE+f"-> {desc} ({score})"+RESET); break
        else: print(RED+"Jawab y/n."+RESET)
    max_score_possible+=max_score; total_score+=score; evaluation_results["Faucet/Modal"]=(score,desc); q_num+=1
    # 5. Funding
    score=0; max_score=5; desc="$0"; print(CYAN+f"\n{q_num}. Funding"+RESET)
    fund=get_float_input(GREEN+"   Jumlah (misal: 5M, 0=T/A): "+RESET,allow_negative=False,default_if_empty=0)
    if fund<=0: score=0; desc="$0/Tdk Tahu"
    elif fund<5e6: score=1; desc=f"< $5M (${fund:,.0f})"
    elif fund<10e6: score=2; desc=f"$5-10M (${fund:,.0f})"
    elif fund<80e6: score=3; desc=f"$10-80M (${fund:,.0f})"
    else: score=5; desc=f">= $80M (${fund:,.0f})"
    print(WHITE+f"-> Funding: {desc} ({score})"+RESET)
    max_score_possible+=max_score; total_score+=score; evaluation_results["Funding"]=(score,desc); q_num+=1
    # 6. Block Explorer
    score=0; max_score=2; desc="Tdk Ada/Kurang"; print(CYAN+f"\n{q_num}. Block Explorer"+RESET)
    while True:
        be=input(GREEN+"   Punya yg berkualitas? (y/n): "+RESET).strip().lower()
        if be=='y': score=2; desc="Berkualitas"; break
        elif be=='n': score=0; desc="Tdk Ada/Kurang"; break
        else: print(RED+"Jawab y/n."+RESET)
    print(WHITE+f"-> Explorer: {desc} ({score})"+RESET)
    max_score_possible+=max_score; total_score+=score; evaluation_results["Block Explorer"]=(score,desc); q_num+=1
    # 7. Tim
    opts={"1":["Good (Publik & Exp)",3],"good":["Good (Publik & Exp)",3],"2":["Sedang (Publik Kurang Info)",2],"sedang":["Sedang (Publik Kurang Info)",2],"3":["Biasa (Info Minim)",1],"biasa":["Biasa (Info Minim)",1],"4":["Anonim/Tdk Tahu",0],"anonim_atau_tidak_diketahui":["Anonim/Tdk Tahu",0]}
    max_score_possible+=3; score,desc=confirm_or_override(ai_model,"Tim",q_num,"Kualitas Tim?",get_s("Kualitas Tim"),opts)
    total_score+=score; evaluation_results["Tim"]=(score,desc); q_num+=1
    # 8. Twitter
    opts={"1":["Verified Kuning",2],"verified_kuning":["Verified Kuning",2],"2":["Verified Biru",1],"verified_biru":["Verified Biru",1],"3":["Standard (Aktif)",1],"standard":["Standard (Aktif)",1],"4":["Tdk Aktif/Ada",0],"tidak_aktif_atau_tidak_ditemukan":["Tdk Aktif/Ada",0]}
    max_score_possible+=2; score,desc=confirm_or_override(ai_model,"Twitter",q_num,"Kualitas Twitter?",get_s("Kualitas Twitter"),opts)
    total_score+=score; evaluation_results["Twitter"]=(score,desc); q_num+=1
    # 9. Telegram
    opts={"1":["Aktif & Pro",1],"aktif_and_profesional":["Aktif & Pro",1],"2":["Biasa",0],"biasa":["Biasa",0],"3":["Tdk Aktif/Ada",0],"tidak_aktif_atau_tidak_ditemukan":["Tdk Aktif/Ada",0]}
    max_score_possible+=1; score,desc=confirm_or_override(ai_model,"Telegram",q_num,"Kualitas Telegram?",get_s("Kualitas Telegram"),opts)
    total_score+=score; evaluation_results["Telegram"]=(score,desc); q_num+=1
    # 10. Discord
    score=0; max_score=5; desc="Tdk Ada/Kualitas"; print(CYAN+f"\n{q_num}. Kualitas Discord"+RESET); print(f"{YELLOW}Saran AI: {get_s('Kualitas Discord')}{RESET}")
    while True:
        d=input(GREEN+"    Discord berkualitas? (y/n): "+RESET).strip().lower()
        if d=='y':
            m=get_float_input(GREEN+"    Jumlah Anggota (misal: 600K): "+RESET,allow_negative=False)
            if m>5e5: score=5; desc=f"Sgt Aktif ({m:,})"
            elif m>1e5: score=3; desc=f"Aktif ({m:,})"
            elif m>1e4: score=1; desc=f"Cukup ({m:,})"
            else: score=0; desc=f"Kurang ({m:,})"
            print(WHITE+f" -> Discord: {desc} ({score})"+RESET); break
        elif d=='n': score=0; desc="Tdk Ada/Kualitas"; print(WHITE+f" -> Discord: {desc} ({score})"+RESET); break
        else: print(RED+"Jawab y/n."+RESET)
    max_score_possible+=max_score; total_score+=score; evaluation_results["Discord"]=(score,desc); q_num+=1
    # 11. Github
    opts={"1":["Aktif & Baik",2],"aktif_and_berkualitas":["Aktif & Baik",2],"2":["Ada Krg Aktif",1],"ada_tapi_kurang_aktif":["Ada Krg Aktif",1],"3":["Tdk Ada",0],"tidak_ditemukan":["Tdk Ada",0]}
    max_score_possible+=2; score,desc=confirm_or_override(ai_model,"Github",q_num,"Kualitas Github?",get_s("Kualitas Github"),opts)
    total_score+=score; evaluation_results["Github"]=(score,desc); q_num+=1
    # 12. Dokumentasi
    opts={"1":["Lengkap & Jelas",2],"lengkap_and_jelas":["Lengkap & Jelas",2],"2":["Ada Krg",1],"ada_tapi_kurang":["Ada Krg",1],"3":["Tdk Ada",0],"tidak_ditemukan":["Tdk Ada",0]}
    max_score_possible+=2; score,desc=confirm_or_override(ai_model,"Dokumentasi",q_num,"Kualitas Dokumentasi?",get_s("Kualitas Dokumentasi"),opts)
    total_score+=score; evaluation_results["Dokumentasi"]=(score,desc); q_num+=1
    # 13. Backer
    opts={"1":["Terkenal",6],"terkenal":["Terkenal",6],"2":["Biasa",3],"biasa":["Biasa",3],"3":["Tdk Tahu",1],"tidak_diketahui":["Tdk Tahu",1]}
    max_score=6; max_score_possible+=max_score; score,desc=confirm_or_override(ai_model,"Backer",q_num,"Reputasi Backer?",get_s("Reputasi Backer/Investor"),opts)
    names=""; desc_backer=desc
    if score>=3: names=input(GREEN+"    Nama backer utama (opsional): "+RESET).strip(); desc_backer=desc+(f" ({names})" if names else "")
    total_score+=score; evaluation_results["Backer/Investor"]=(score,desc_backer); q_num+=1
    # 14. Anti-Sybil
    score=0; max_score=1; desc="Tdk Ada"; print(CYAN+f"\n{q_num}. Anti-Sybil"+RESET)
    while True:
        s=input(GREEN+"   Ada indikasi anti-sybil? (y/n): "+RESET).strip().lower()
        if s=='y': score=1; desc="Ada Indikasi"; break
        elif s=='n': score=0; desc="Tdk Ada"; break
        else: print(RED+"Jawab y/n."+RESET)
    print(WHITE+f"-> Anti-Sybil: {desc} ({score})"+RESET)
    max_score_possible+=max_score; total_score+=score; evaluation_results["Anti-Sybil"]=(score,desc); q_num+=1
    # 15. Jenis Airdrop
    print(CYAN+f"\n{q_num}. Jenis Airdrop"+RESET)
    opts={"1":("Testnet",6),"2":("Web3",3),"3":("Ekstensi",4),"4":("App",4),"5":("Node",5),"6":("Role",5)}
    opts_str="\n".join([f"   {WHITE}{k}.{RESET} {v[0]} ({v[1]})" for k,v in opts.items()]); print(opts_str)
    jenis="N/A"; score=0; desc="N/A"; max_score=6
    while True:
        o=input(GREEN+"   Pilih jenis (1-6): "+RESET).strip()
        if o in opts: jenis, score=opts[o]; desc=jenis; break
        else: print(RED+"Pilih 1-6."+RESET)
    print(WHITE+f"-> Jenis: {desc} ({score})"+RESET)
    max_score_possible+=max_score; total_score+=score; evaluation_results["Jenis Airdrop"]=(score,desc); q_num+=1
    # --- Review Step ---
    print(CYAN+"\n"+"="*50+RESET); print(CYAN+BOLD+" REVIEW EVALUASI BAGIAN 1 ".center(50,'=')+RESET); print(CYAN+"="*50+RESET)
    print(f"{GREEN}{'Kriteria':<25} : {WHITE}{'Penilaian Anda':<40} (Skor){RESET}"); print(f"{CYAN}{'-'*25} : {'-'*40}------{RESET}")
    for k,(s,d) in evaluation_results.items(): score_str=f"({s})" if k not in ["Nama Proyek","URL Proyek"] else ""; print(f"{GREEN}{k:<25} : {WHITE}{d:<40} {score_str}{RESET}")
    persen_rev=(total_score/max_score_possible)*100 if max_score_possible>0 else 0
    print(f"\n{GREEN}{'TOTAL SKOR':<25} : {WHITE}{total_score} / {max_score_possible}{RESET}"); print(f"{GREEN}{'PERSENTASE':<25} : {WHITE}{persen_rev:.1f}%{RESET}"); print(CYAN+"="*50+RESET)
    while True:
        konfirm=input(GREEN+"\nApakah hasil evaluasi benar? (y/n): "+RESET).strip().lower()
        if konfirm=='y': print(GREEN+"[OK] Konfirmasi OK."+RESET); confirmed=True; break
        elif konfirm=='n': print(YELLOW+"[!] OK, mengulang Bagian 1..."+RESET); confirmed=False; break
        else: print(RED+"Jawab y/n."+RESET)
    if not confirmed: return None
    persen=persen_rev; rating="Kurang 📉"
    if persen>=80: rating="Sangat Potensi 🔥"
    elif persen>=70: rating="Potensi 👍"
    elif persen>=50: rating="Cukup 🤔"
    print(f"\n{GREEN}Rating Final:{RESET} {WHITE}{rating} ({persen:.1f}%){RESET}")
    return evaluation_results.get("Nama Proyek",(0,"N/A"))[1], evaluation_results.get("Jenis Airdrop",(0,"N/A"))[1], persen, rating

# --- Fungsi Prediksi Reward & Harga ---
def get_float_input(prompt, allow_negative=False, allow_zero=True, default_if_empty=None):
    while True:
        try:
            val_str = input(prompt).strip()
            if not val_str:
                if default_if_empty is not None: print(f"{CYAN}[Info] Default: {default_if_empty}{RESET}"); return float(default_if_empty)
                else: print(RED + "[X] Input kosong." + RESET); continue
            val_str_upper = val_str.upper(); mult = 1; num_part = val_str_upper
            if val_str_upper.endswith('M'): mult = 1e6; num_part = val_str_upper[:-1]
            elif val_str_upper.endswith('K'): mult = 1e3; num_part = val_str_upper[:-1]
            value = float(num_part) * mult
            if not allow_negative and value < 0: print(RED + "[X] Tidak boleh negatif." + RESET)
            elif not allow_zero and value == 0: print(RED + "[X] Tidak boleh nol." + RESET)
            else: return value
        except ValueError: print(RED + "[X] Input angka (opsi K/M)." + RESET)
        except Exception as e: print(RED + f"[X] Error: {e}" + RESET)

def prediksi_reward():
    print(CYAN+"\n"+"="*50+RESET); print(CYAN+BOLD+" BAGIAN 2: PREDIKSI REWARD TOKEN ".center(50,'=')+RESET); print(CYAN+"="*50+RESET)
    print(f"{GREEN}Pilih Metode:{RESET} 1.Pro Rata 2.Piecewise/Tiered 3.Manual")
    token_value = 0.0; reward_output = "N/A"; reward_method = "N/A"
    while True:
        pilihan = input(GREEN + "Metode (1/2/3): " + RESET).strip()
        if pilihan == "1":
            reward_method = "Pro Rata"; print(CYAN+"\n--- Pro Rata ---"+RESET)
            while True:
                tahu = input(GREEN+"Tahu total poin? (y/n): "+RESET).strip().lower()
                if tahu == 'y':
                    total_poin = get_float_input(GREEN+"  Total Poin Semua  : "+RESET, allow_zero=False)
                    poin_ind = get_float_input(GREEN+"  Poin Anda         : "+RESET, allow_zero=True)
                    total_sup = get_float_input(GREEN+"  Total Supply Token: "+RESET, allow_zero=False)
                    alloc_perc = get_float_input(GREEN+"  % Alokasi Airdrop : "+RESET, allow_negative=False) / 100.0
                    if total_poin>0 and total_sup>0 and alloc_perc>=0: token_value=(poin_ind/total_poin)*(total_sup*alloc_perc); reward_output=f"{token_value:,.4f} token"
                    else: token_value=0.0; reward_output="Gagal Hitung"; print(RED+"Periksa input."+RESET)
                    break
                elif tahu == 'n':
                    print(CYAN+"[Info] Estimasi manual."+RESET); token_value=get_float_input(GREEN+"  Estimasi Token: "+RESET,allow_negative=False)
                    reward_output=f"{token_value:,.4f} token"; reward_method="Manual (Estimasi)"; break
                else: print(RED+"Jawab y/n."+RESET)
            break
        elif pilihan == "2":
            reward_method = "Piecewise"; print(CYAN+"\n--- Piecewise/Tiered ---"+RESET)
            B = get_float_input(GREEN + "  Jumlah Badge/Level: " + RESET, allow_negative=False)
            if B < 5:   token_value = 10.0
            elif B < 10:  token_value = 50.0
            elif B < 20:  token_value = 150.0
            else:         token_value = 300.0
            reward_output = f"{token_value:,.4f} token"; print(WHITE + f" -> Estimasi: {reward_output}"+ RESET); break
        elif pilihan == "3":
            reward_method = "Manual"; print(CYAN+"\n--- Manual ---"+RESET)
            token_value = get_float_input(GREEN+"  Estimasi Token: "+RESET, allow_negative=False); reward_output = f"{token_value:,.4f} token"; break
        else: print(RED+"Pilihan 1/2/3."+RESET)
    print(f"\n{GREEN}Hasil Prediksi Reward:{RESET} {WHITE}{reward_output} ({reward_method}){RESET}")
    return reward_output, float(token_value), reward_method

def prediksi_harga():
    print(CYAN+"\n"+"="*50+RESET); print(CYAN+BOLD+" BAGIAN 3: PREDIKSI HARGA TOKEN ".center(50,'=')+RESET); print(CYAN+"="*50+RESET)
    total_supply = get_float_input(GREEN + "Total Supply Token: " + RESET, allow_zero=False)
    market_cap_proj = 0.0; price_method = "N/A"
    print(f"\n{GREEN}Pilih Metode Prediksi MC:{RESET} 1.Opsi Umum 2.Manual")
    while True:
        pilihan_mc = input(GREEN + "Metode MC (1/2): " + RESET).strip()
        if pilihan_mc == "1":
            price_method = "Opsi Umum"; print(CYAN+"\n--- Opsi MC Umum ---"+RESET)
            opts = {"1":("$20M",20e6),"2":("$50M",50e6),"3":("$100M",100e6),"4":("$200M",200e6),"5":("$500M",500e6),"6":("$1B",1e9)}
            opts_str="\n".join([f"  {WHITE}{k}.{RESET} {v[0]}" for k,v in opts.items()]); print(opts_str)
            while True:
                o = input(GREEN + "Pilih Opsi MC (1-6): " + RESET).strip()
                if o in opts: market_cap_proj = opts[o][1]; print(WHITE+f"-> MC: {opts[o][0]}"+RESET); break
                else: print(RED+"Pilih 1-6."+RESET)
            break
        elif pilihan_mc == "2":
            price_method = "Manual"; print(CYAN+"\n--- Manual MC ---"+RESET)
            market_cap_proj = get_float_input(GREEN+"  Proyeksi MC (misal: 150M): "+RESET, allow_negative=False, allow_zero=False)
            print(WHITE+f"-> MC manual: ${market_cap_proj:,.0f}"+RESET); break
        else: print(RED+"Pilihan 1/2."+RESET)
    predicted_price = market_cap_proj / total_supply if total_supply > 0 else 0.0
    print(f"\n{GREEN}Hasil Prediksi Harga:{RESET}")
    print(f"{GREEN}  Total Supply :{RESET} {WHITE}{total_supply:,.0f}{RESET}")
    print(f"{GREEN}  Proyeksi MC  :{RESET} {WHITE}${market_cap_proj:,.0f} ({price_method}){RESET}")
    print(f"{GREEN}{BOLD}  Prediksi Harga:{RESET} {WHITE}${predicted_price:,.6f}{RESET}")
    return predicted_price

# --- Fungsi Feedback & Summary ---
def confirmed_feedback():
    print(CYAN+"\n"+"="*50+RESET); print(CYAN+BOLD+" BAGIAN 4: FEEDBACK TAMBAHAN ".center(50,'=')+RESET); print(CYAN+"="*50+RESET)
    return input(GREEN + "Feedback / Catatan (opsional):\n" + RESET).strip()

def remove_html_tags(text): return re.sub(re.compile('<.*?>'), '', text)

def print_summary(lines):
    if not lines: return
    print(CYAN+"\n"+BOLD+"="*50+RESET); print(CYAN+BOLD+" RINGKASAN AKHIR ANALISIS ".center(50,'=')+RESET); print(CYAN+BOLD+"="*50+RESET)
    max_len = 0; plain_lines = [remove_html_tags(line) for line in lines]
    if plain_lines:
        try: max_len = max(len(line.split(':', 1)[0]) for line in plain_lines if ':' in line)
        except ValueError: max_len = 20
    for line in plain_lines:
         if ':' in line: parts=line.split(':',1); key=parts[0].strip(); value=parts[1].strip(); print(f"{GREEN}{key:<{max_len}} :{RESET} {WHITE}{value}{RESET}")
         else: print(f"{CYAN}{line}{RESET}")
    print(CYAN+BOLD+"="*50+RESET)

# --- FUNGSI UTAMA (MAIN) ---
def main():
    run_analysis = True
    while run_analysis:
        try:
            tampilkan_logo()
            config_data = load_configuration_files()
            part1_result = part1(config_data)
            if part1_result is None: print(YELLOW+"\nMengulang Bagian 1...\n"+RESET); continue
            proyek, jenis, persen, rating = part1_result
            reward_str, token_val, reward_method = prediksi_reward()
            price_val = prediksi_harga()
            total_reward_val = token_val * price_val
            feedback = confirmed_feedback()
            # Persiapan Data
            timestamp = datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec='seconds')
            record = [ timestamp, proyek, jenis, f"{persen:.1f}", rating, f"{token_val:.4f}", f"{price_val:.6f}", f"{total_reward_val:.2f}", feedback ]
            summary = [ f"<b>📊 Ringkasan Analisis 📊</b>", f"------------------------------------", f"<b>Nama Proyek</b>     : {proyek}", f"<b>Jenis Airdrop</b>   : {jenis}", f"<b>Rating Proyek</b>   : {rating} ({persen:.1f}%)", f"------------------------------------", f"<b>Prediksi Token</b>  : {reward_str} <i>({reward_method})</i>", f"<b>Prediksi Harga</b>  : ${price_val:,.6f}", f"<b>Total Reward Est</b>: ${total_reward_val:,.2f}", f"------------------------------------", f"<i>Timestamp: {timestamp}</i>" ]
            if feedback: summary.insert(-1, f"<b>Catatan</b>         : {feedback}")
            # Output
            print_summary(summary)
            kirim_ke_telegram("\n".join(summary), config_data)
            send_to_sheets(record, "analysis", config_data)
            print(GREEN+BOLD+"\n✅ Analisis Selesai!"+RESET); run_analysis = False
        except KeyboardInterrupt: print(f"\n{YELLOW}{BOLD}Program dihentikan.{RESET}"); run_analysis = False
        except Exception as e:
             print(f"\n{RED}{BOLD}[!!!] Error Tidak Terduga: {e}{RESET}")
             print(YELLOW + "--- Traceback ---"); traceback.print_exc(); print(YELLOW + "-----------------" + RESET)
             while True:
                  retry = input(YELLOW+"Coba jalankan ulang? (y/n): "+RESET).strip().lower()
                  if retry == 'y': run_analysis = True; break
                  elif retry == 'n': run_analysis = False; print(CYAN+"Program diakhiri."+RESET); break
                  else: print(RED+"Jawab y/n."+RESET)

# --- ENTRY POINT ---
if __name__ == "__main__":
    main()
