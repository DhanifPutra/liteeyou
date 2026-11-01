<p align="center">
  <img src="logo.webp" alt="YouTube Lite Logo" width="120" />
</p>

<h1 align="center">YouTube Lite</h1>

<p align="center">
  Aplikasi Desktop Pemutar dan Pengunduh YouTube Berbasis PySide6, MPV Native, dan HTML5 UI.
</p>

---

## Deskripsi

YouTube Lite adalah aplikasi pemutar video desktop yang dirancang untuk memberikan pengalaman menonton YouTube yang cepat, mulus, dan bebas lag. Menggabungkan arsitektur antarmuka modern HTML5, CSS3, dan JavaScript dengan akselerasi perangkat keras MPV Player serta backend Python PySide6, aplikasi ini berjalan efisien tanpa beban berat peramban web penuh.

Dilengkapi dengan sistem Download Manager mandiri yang mendukung pengunduhan video MP4 dalam berbagai pilihan resolusi (1080p Full HD, 720p HD, 480p, 360p) serta ekstraksi audio MP3 kualitas tinggi.

---

## Fitur Utama

- Antarmuka Modern dan Responsif: Desain gelap (Dark Mode) berbasis HTML5/CSS3 dengan animasi transisi kartu, status skeleton loading, dan tata letak yang bersih.
- Pemutar Video Terintegrasi: Ditenagai engine native MPV (libmpv) dengan akselerasi perangkat keras, latensi ultra-rendah, kontrol pintasan keyboard lengkap (F / F11 untuk layar penuh, spasi untuk jeda/putar).
- Pengelola Unduhan Mandiri (Download Manager):
  - Halaman khusus antrean unduhan dengan navigasi langsung dari bilah atas atau menu pemutar.
  - Pilihan format dan resolusi video: MP4 1080p, MP4 720p, MP4 480p, MP4 360p, dan Audio MP3 (192 kbps).
  - Penggabungan otomatis trek video dan audio menjadi file tunggal yang siap diputar menggunakan FFmpeg.
  - Pemantauan progres real-time: persentase (1-100 persen), kecepatan unduh (MB/s), ukuran file, dan estimasi waktu sisa (ETA).
  - Kontrol unduhan interaktif: tombol jeda (pause), lanjutkan (resume), batal (cancel), dan buka folder tujuan.
- Beranda dan Filter Kategori: Akses cepat ke kategori Trending, Musik, Gaming, Teknologi, Edukasi, dan Berita.
- Pencarian Fleksibel: Temukan konten berdasarkan kata kunci pencarian atau langsung masukkan tautan URL video YouTube.
- Bookmark Channel Favorit: Simpan channel pilihan secara lokal untuk melihat katalog video terbaru channel kapan saja.
- Riwayat Tontonan: Menyimpan riwayat video yang pernah diputar secara otomatis di penyimpanan lokal komputer Anda.

---

## Prasyarat Sistem

- Sistem Operasi: Windows 10 atau Windows 11 (64-bit)
- Python: Versi 3.10 atau yang lebih baru (arsitektur 64-bit)
- Node.js: Disarankan terinstal pada sistem (dibutuhkan oleh engine yt-dlp untuk parsing JavaScript YouTube)
- Koneksi Internet

---

## Persiapan File Eksternal (Folder tools/)

Demi menjaga kepatuhan batas ukuran file repositori GitHub (maksimum 100 MB per file), file biner eksternal tidak disimpan di dalam repositori Git. Sebelum menjalankan aplikasi, letakkan file biner 64-bit berikut di dalam direktori `tools/`:

1. `libmpv-2.dll` (dan file dependensi MPV terkait)
   - Dapat diunduh dari rilis Windows libmpv (misalnya build shinchiro/mpv-winbuild atau sourceforge mpv).
2. `yt-dlp.exe`
   - Unduh versi terbaru dari rilis resmi GitHub: `https://github.com/yt-dlp/yt-dlp/releases`
3. `ffmpeg.exe`
   - Unduh build static essentials dari: `https://www.gyan.dev/ffmpeg/builds/` (pastikan mendukung encoder libmp3lame dan libx264).

Struktur folder `tools/` setelah dilengkapi:
```text
tools/
├── include/
├── ffmpeg.exe
├── libmpv-2.dll
├── yt-dlp.conf
├── yt-dlp.exe
└── .gitkeep
```

---

## Panduan Instalasi dan Penggunaan

### 1. Klon Repositori
```bash
git clone https://github.com/<username>/<nama-repo>.git
cd youtube_lite_starter
```

### 2. Pemasangan Otomatis (Windows)
Jalankan file batch instalasi yang telah disediakan:
```bash
setup_windows.bat
```
Skrip ini akan secara otomatis membuat virtual environment di folder `.venv`, memperbarui pip, dan memasang pustaka yang tercantum dalam `requirements.txt`.

### 3. Pemasangan Manual
Jika ingin melakukan pengaturan secara manual via terminal / PowerShell:
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Menjalankan Aplikasi
Setelah paket dependensi dan file biner `tools/` lengkap, jalankan aplikasi melalui:
```bash
run_windows.bat
```
Atau menggunakan terminal:
```bash
.\.venv\Scripts\python.exe main.py
```

### 5. Membuat File Eksekusi Portabel (Build EXE)
Untuk mengemas seluruh aplikasi menjadi paket executable mandiri di folder `dist/`:
```bash
build_exe.bat
```
File executable `YouTubeLite.exe` akan dihasilkan di dalam direktori `dist/YouTubeLite/`.

---

## Kebijakan Berkas Git (.gitignore)

Repositori ini telah dikonfigurasi dengan aturan `.gitignore` yang ketat untuk menjaga keamanan, efisiensi ukuran, dan kebersihan kode:

### Berkas yang Diabaikan (Tidak Diunggah ke GitHub):
- Lingkungan Python: `.venv/`, `env/`, `__pycache__/`, `*.pyc`
- File Kompilasi dan Build: `dist/`, `build/`, `*.egg-info/`
- Berkas Biner Berukuran Besar: `tools/*.dll`, `tools/*.exe`, `tools/*.jar`, `tools/*.a`
- Berkas Data Pengguna dan Unduhan: `bookmarks.json`, `history.json`, `downloads/`, `*.part`, `*.ytdl`, `*.log`, `*.mp4`, `*.mp3`, `*.webm`, `*.m4a`
- Konfigurasi Editor dan Sistem: `.vscode/`, `.idea/`, `.DS_Store`, `Thumbs.db`

### Berkas yang Disimpan di Repositori:
- Seluruh kode sumber backend (`main.py`, skrip konfigurasi `requirements.txt`, `YouTubeLite.spec`, file batch `.bat`).
- Aset antarmuka web (`web/index.html`, `web/style.css`, `web/app.js`, `web/components/*.html`).
- Aset gambar dan branding resmi (`logo.webp`, `web/logo.webp`).
- Konfigurasi dasar tools (`tools/yt-dlp.conf`, `tools/LICENSE.LGPL`, `tools/.gitkeep`).

---

## Lisensi

Proyek ini menggunakan lisensi perangkat lunak terbuka. Komponen pemutar media MPV dan yt-dlp tunduk pada ketentuan lisensi masing-masing (LGPL/GPL/Unlicense).
