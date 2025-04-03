<<<<<<< HEAD
# Proyek Integrasi Telegram, Google Sheets & Airdrop Tools

Proyek ini merupakan kumpulan script Python yang mengintegrasikan berbagai alat untuk mengelola data dan melakukan analisis terkait airdrop. Aplikasi ini terhubung ke Telegram untuk mengirim notifikasi dan ke Google Sheets untuk menyimpan serta mengupdate data secara otomatis.

> **Catatan:** Kode sumber telah diobfuscate menggunakan [PyArmor](https://pyarmor.readthedocs.io/) untuk melindungi logika internal. Jangan mendistribusikan kode sumber asli.

---

## Daftar Modul

Proyek ini terdiri dari **9 modul** utama, masing-masing dengan fungsi khusus:

1. **Reshareshing Tools**  
   - **Fungsi:**  
     Mengumpulkan data interaktif dari pengguna melalui terminal, menampilkan preview data, mengirim ringkasan ke Telegram, dan menyimpan data ke Google Sheets.
   - **Fitur:**  
     - Input data interaktif.
     - Validasi dan penyimpanan lokal.
     - Notifikasi ke Telegram dan update otomatis ke Google Sheets.

2. **Datacurator / DROPXJUNGLER**  
   - **Fungsi:**  
     Menampilkan animasi ASCII art dengan efek shimmer dan menggabungkan data dari berbagai sumber ke Google Sheets.
   - **Fitur:**  
     - Tampilan terminal interaktif.
     - Efek warna dan animasi.
     - Update marker "M" pada baris tertentu di Google Sheets.
3. **Analysis Tool**  
   - **Fungsi:**  
     Menghitung skor evaluasi proyek airdrop, memprediksi reward dan harga token, serta mengirim ringkasan hasil evaluasi ke Telegram dan Google Sheets.
   - **Fitur:**  
     - Perhitungan total skor dan persentase.
     - Prediksi reward dengan beberapa metode (misalnya, pro rata, piecewise function).
     - Notifikasi ke Telegram dan penyimpanan ke Google Sheets.

4. **Moderator Tools**  
   - **Fungsi:**  
     Menggabungkan data dari beberapa spreadsheet (Reshareshing, Analysis, Strategy) ke spreadsheet moderator dan menyediakan menu interaktif untuk input data serta update list airdrop.
   - **Fitur:**  
     - Penggabungan data dari berbagai sumber.
     - Update marker dan feedback melalui menu interaktif.
     - Notifikasi ke Telegram.

5. **Monitoring Tool**  
   - **Fungsi:**  
     Memantau aktivitas harian, mingguan, dan bulanan dengan menghitung marker dari sheet yang diupdate, menyimpan hasil monitoring ke Google Sheets, dan mengirim notifikasi.
   - **Fitur:**  
     - Penghitungan interaksi berdasarkan kategori.
     - Pembersihan data mentah (delete baris) setelah perhitungan.
     - Notifikasi monitoring ke Telegram.

6. **Script Tool**  
   - **Fungsi:**  
     Menerima input nama script dan link GitHub, lalu mengirim data tersebut ke Google Sheets (ditulis pada baris genap dengan marker "M") dan mengirim notifikasi ke Telegram.
   - **Fitur:**  
     - Input data script.
     - Update otomatis ke Google Sheets.
     - Notifikasi update melalui Telegram.

7. **Strategy Tool**  
   - **Fungsi:**  
     Menyediakan panduan langkah pengerjaan tugas (swap, bridge, faucet, dll), menampilkan logo dan panduan anti-sybil, serta mengirim ringkasan hasil (termasuk feedback) ke Telegram dan Google Sheets.
   - **Fitur:**  
     - Tampilan logo interaktif dan panduan langkah.
     - Petunjuk anti-sybil.
     - Notifikasi dan update data ke Google Sheets.
 8. **Supervisormode**
   - **Fungsi:**  
     Menjalankan automasi untuk mengelola berbagai role, menyalin data antar spreadsheet, menghitung total data monitoring, dan menyediakan utilitas untuk membersihkan data (clear data utility) untuk supervisor dan role.
   - **Fitur:**  
     - Eksekusi otomatis script untuk role.
     - Penyalinan data antar spreadsheet.
     - Proses monitoring dan clear data.

---

## Fitur Utama

- **Integrasi Telegram:** Mengirim pesan notifikasi dan ringkasan data ke channel atau thread Telegram.
- **Integrasi Google Sheets:** Update data secara otomatis, penulisan header, dan penambahan marker di baris genap.
- **User-Friendly Terminal Interface:** Tampilan interaktif dengan warna dan animasi untuk kemudahan penggunaan.
---

## Instalasi & Setup

1. **Clone repositori:**
   ```bash
   git clone https://github.com/username/nama-proyek.git
   cd nama-proyek
Berikut adalah bagian "Instalasi & Setup" yang lebih lengkap dan mendetail untuk README.md:

---

### Instalasi & Setup

Pastikan sistem Anda sudah memenuhi prasyarat berikut:
- **Python 3.7+** telah terinstal.
- **Git** untuk mengkloning repositori.
- Akses internet untuk mengunduh dependensi.

#### 1. Clone Repositori

Buka terminal (atau Command Prompt/PowerShell di Windows) dan jalankan perintah berikut untuk mengkloning repositori:

bash
git clone https://github.com/frendicahyow/DROPXJUNGLER.git
cd DROPXJUNGLER


#### 2. Buat Virtual Environment

Disarankan untuk menggunakan virtual environment agar dependensi proyek tidak bercampur dengan paket sistem. Gunakan perintah berikut sesuai dengan sistem operasi Anda:

- **Linux/MacOS:**

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- **Windows:**

  bash
  python -m venv venv
  venv\Scripts\activate
Setelah virtual environment aktif, prompt terminal biasanya akan diawali dengan `(venv)`.

#### 3. Instalasi Dependensi

Instal semua paket yang diperlukan menggunakan file `requirements.txt`:

bash
pip install -r requirements.txt


Pastikan tidak ada error selama proses instalasi. Jika ada masalah, pastikan versi pip Anda sudah terbaru dengan menjalankan:

bash
pip install --upgrade pip


#### 4. Konfigurasi File

Pastikan Anda telah membuat dan mengisi file-file konfigurasi berikut di direktori root proyek (atau sesuai instruksi masing-masing modul):

- **token.txt:**  
  Masukkan token bot Telegram.

- **Idchat.txt:**  
  Masukkan ID chat Telegram (atau channel/kelompok).

- **Threads.txt:**  
  Jika menggunakan thread pada Telegram, masukkan ID thread di sini. Jika tidak, file ini dapat dikosongkan.

- **credentials.json:**  
  File kredensial untuk Google Service Account. Pastikan file ini sudah dikonfigurasi untuk mengakses Google Sheets API dan Drive API (jika diperlukan).

- **spreadsheet_id.txt:**  
  Masukkan ID Google Spreadsheet utama (misalnya untuk modul Reshareshing, Analysis, Strategy).

- **datacuratorid.txt:**  
  (Opsional) Jika modul Datacurator menggunakan spreadsheet berbeda, masukkan ID-nya di sini.

- **copyid.txt:**  
  Berisi daftar ID spreadsheet sumber untuk penggabungan data pada modul Moderator Tools. Formatnya biasanya:
  
  NamaSheet1: ID_Spreadsheet1
  NamaSheet2: ID_Spreadsheet2
  

- **proofworkid.txt:**  
  Masukkan ID Google Spreadsheet untuk Proofwork Module.

- **namesheet.txt:**  
  Daftar nama sheet yang akan digunakan oleh Proofwork Module, satu per baris.

- **Linkgsmoderator.txt:**  
  Masukkan URL lengkap (atau ID) dari spreadsheet moderator.

- **Linkgs.txt:**  
  Masukkan daftar URL spreadsheet untuk Reshareshing, Analysis, dan Strategy. Pastikan ada minimal 3 URL (satu per modul).

- **Linkgslistairdrop.txt:**  
  Masukkan URL untuk list airdrop jika modul ini digunakan.

- **mospreadsheet_id.txt:**  
  File yang berisi pasangan key:value untuk ID spreadsheet yang digunakan pada Monitoring Tool. Format:  

  Reshareshing: ID1
  Analysis: ID2
  
  

- **monitoringid.txt:**  
  Masukkan ID Google Spreadsheet yang akan digunakan untuk menyimpan hasil monitoring.

- **idsupervisor.txt:**  
  Masukkan ID spreadsheet supervisor untuk Supervisor Mode.

- **sheetid.txt:**  
  File yang berisi pasangan key:value untuk ID spreadsheet yang digunakan di Supervisor Mode (misalnya untuk clear data dan role).

Pastikan setiap file konfigurasi berisi data yang benar dan tersimpan di lokasi yang tepat.


#### 6. Menjalankan Modul

Setiap modul bisa dijalankan secara independen. Contoh perintah untuk menjalankan modul tertentu:

- **Reshareshing Tools:**
  bash
  python bot.py
  
- **Datacurator / DROPXJUNGLER:**
  bash
  python bot.py
  
- **Analysis Tool:**
  bash
  python bot.py
  
- **Moderator Tools:**
  bash
  python bot.py
  
- **Monitoring Tool:**
 bash
  python bot.py

- **Script Tool:**
 bash
  python bot.py
  
- **Strategy Tool:**
  bash
  python bot.py
 
- **Supervisor Mode:**
  bash
  python bot.py


> **Catatan:** Ganti nama file sesuai dengan modul yang tersedia di proyek Anda.

#### 7. Troubleshooting

- **Kredensial Google:**  
  Pastikan file `credentials.json` sudah memiliki izin yang tepat untuk mengakses Google Sheets API dan Drive API jika diperlukan.

- **Konfigurasi Telegram:**  
  Pastikan file `token.txt`, `Idchat.txt`, dan `Threads.txt` berisi data yang valid.

- **Koneksi Internet:**  
  Pastikan koneksi internet Anda stabil karena script akan melakukan request ke API Google dan Telegram.


---

Ikuti langkah-langkah di atas secara berurutan untuk memastikan setup berjalan dengan lancar. Jika terdapat error, periksa kembali file konfigurasi dan pastikan semua dependensi telah terinstal dengan benar.

Semoga panduan instalasi & setup ini membantu!

untuk informasi lebih mendalam silahkan DM saya di ig 
=======
# DROPXJUNGLER
>>>>>>> 655723fc870c01d67eb918927a46b53572026891
