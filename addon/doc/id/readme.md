# NusaNews - Pembaca Berita Indonesia untuk NVDA

Add-on NusaNews memungkinkan Anda untuk memantau dan membaca berita terbaru secara langsung dan aksesibel dari berbagai portal berita terkemuka di Indonesia menggunakan pembaca layar NVDA. Dengan fitur utama **Offline Reader Mode**, Anda dapat membaca isi lengkap artikel berita secara offline langsung di dalam dialog NVDA yang nyaman tanpa perlu membuka browser web eksternal yang sering kali dipenuhi dengan iklan, popup, dan elemen yang mengganggu aksesibilitas.

## Fitur Utama

*   **Pintasan Keyboard Tunggal**: Tekan `NVDA+Shift+/` dari mana saja untuk memunculkan dialog utama pembaca berita.
*   **Offline Reader Mode (Mode Membaca Offline)**: Membuka dan membaca isi lengkap artikel berita dalam kotak teks multi-baris yang ramah pembaca layar. Anda dapat membaca artikel baris demi baris menggunakan tombol panah atas/bawah standard.
*   **8 Sumber Berita Populer**:
    *   *Berita Umum*: Detik.com, Kompas.com, Antara News, Republika, Liputan6, Merdeka.com, dan CNN Indonesia.
    *   *Berita Teknologi*: WinPoin (berita Windows/Microsoft).
*   **Kategori Berita Terstruktur**: Nasional, Internasional, Teknologi, Politik, Ekonomi, Olahraga, Entertainment, dan Disabilitas.
*   **Penyaringan Khusus Isu Disabilitas**: Ketika memilih kategori "Disabilitas", add-on secara otomatis menyaring berita dari semua portal menggunakan daftar kata kunci relevan disabilitas yang komprehensif. Ini memastikan daftar berita hanya berisi informasi yang benar-benar berkaitan dengan isu disabilitas di Indonesia.
*   **Sistem Notifikasi Pintar**:
    *   *Hanya Ringkasan (Digest)*: Mengumumkan jumlah berita baru yang masuk selama siklus pencarian otomatis.
    *   *Berita Langsung (Immediate)*: Mengumumkan judul berita baru satu per satu begitu ditemukan (maksimal 5 judul per siklus untuk mencegah banjir suara).
*   **Jam Sunyi (Do Not Disturb - DND)**: Mematikan notifikasi berita otomatis pada rentang jam tertentu (misalnya malam hari) agar tidak mengganggu istirahat Anda.
*   **Pagination (Muat Lebih Banyak)**: Membatasi jumlah awal tampilan berita (20, 50, atau 100) dan menyediakan opsi `-- Muat Lebih Banyak --` di akhir daftar berita untuk memuat berita berikutnya secara instan dan memindahkan fokus secara otomatis ke berita baru pertama.
*   **Penyimpanan Cache Lokal**: Artikel yang sudah diunduh akan disimpan secara lokal, sehingga dapat dibaca kembali secara instan.
*   **Bypass SSL Verification**: Opsi darurat untuk melewati verifikasi SSL jika koneksi internet Anda mengalami masalah sertifikat lokal.

---

## Panduan Penggunaan dan Pintasan Keyboard

### 1. Dialog Utama Pembaca Berita
Untuk membuka NusaNews, tekan **`NVDA+Shift+/`** dari mana saja. Dialog utama akan terbuka dan fokus akan langsung berada pada daftar berita.
*   **Navigasi Berita**: Gunakan tombol **Panah Atas** dan **Panah Bawah** untuk memilih artikel berita.
*   **Membuka Artikel**: Tekan **Enter** atau klik dua kali pada berita yang dipilih untuk membuka **Reader Mode** offline.
*   **Salin Link (Alt+C)**: Menyalin tautan berita (URL) yang dipilih ke clipboard.
*   **Tandai Dibaca (Alt+D)**: Menandai berita yang dipilih saat ini sebagai sudah dibaca (menghilangkan awalan `[Baru]`).
*   **Tandai Semua Dibaca (Alt+M)**: Menandai seluruh berita yang tampil dalam daftar saat ini sebagai sudah dibaca.
*   **Segarkan Berita (Alt+S)**: Memicu proses pencarian berita baru secara manual dari seluruh sumber yang aktif.
*   **Salin Link (Alt+L)**: Salin URL berita yang dipilih.
*   **Tutup Dialog (Alt+T atau Escape)**: Menutup dialog NusaNews dan kembali ke aplikasi sebelumnya.
*   **Filter Sumber dan Kategori**: Gunakan tombol **Tab** untuk berpindah ke dropdown filter sumber atau kategori, lalu gunakan tombol **Panah** untuk mengubah penyaringan. Daftar berita akan terupdate secara instan.

### 2. Jendela Reader Mode (Membaca Offline)
Ketika Anda membuka berita, dialog bacaan akan tampil dengan kotak teks baca-saja. NVDA akan langsung menaruh fokus pada kotak teks ini untuk mulai membacanya.
*   **Membaca Teks**: Gunakan tombol panah standar pembaca layar (seperti **Panah Bawah**, **Panah Atas**, **Page Down**, dll) untuk membaca artikel baris demi baris atau paragraf demi paragraf.
*   **Buka di Browser (Alt+B)**: Jika Anda ingin melihat halaman web asli artikel tersebut, tekan tombol ini untuk membukanya di browser internet default Anda.
*   **Salin Link (Alt+L)**: Menyalin tautan berita (URL) saat ini ke clipboard.
*   **Salin ke Clipboard (Alt+S)**: Menyalin seluruh isi lengkap artikel (termasuk judul dan metadata) ke clipboard sistem agar bisa ditempel di aplikasi lain.
*   **Tutup Pembaca (Alt+T atau Escape)**: Menutup jendela bacaan offline dan kembali ke daftar utama NusaNews.

---

## Konfigurasi Pengaturan NusaNews

Anda dapat menyesuaikan perilaku add-on ini melalui menu Pengaturan NVDA:
1.  Tekan **`NVDA+N`** untuk membuka menu NVDA.
2.  Pilih **Preferences** -> **Settings...** (Pengaturan).
3.  Di dalam daftar kategori sebelah kiri, cari dan pilih **nusaNewsID**.
4.  Gunakan tombol **Tab** untuk berpindah di antara pilihan pengaturan berikut:

*   **Sumber Berita Aktif**: Centang atau hilangkan centang pada nama-nama portal berita (Detik, Kompas, Antara, Republika, Liputan6, Merdeka, CNN Indonesia, WinPoin) yang ingin dipantau.
*   **Interval Penyegaran (menit)**: Memilih seberapa sering add-on mencari berita baru di latar belakang (2, 5, 10, 15, 30, 60, atau 120 menit).
*   **Mode Notifikasi**:
    *   *Hanya Ringkasan (Digest)*: NVDA hanya mengumumkan ringkasan jumlah berita (contoh: *"NusaNews: 5 berita baru tersedia"*).
    *   *Berita Langsung (Immediate)*: NVDA mengumumkan judul-judul berita baru secara bergantian.
*   **Mainkan nada notifikasi ketika ada berita baru**: Centang pilihan ini untuk memainkan bunyi bip pendek setiap kali berita baru masuk.
*   **Utamakan berita breaking news**: Jika dicentang, berita berlabel breaking news akan selalu diumumkan secara langsung terlepas dari setelan mode notifikasi.
*   **Aktifkan Jam Sunyi (Do Not Disturb)**: Centang pilihan ini untuk menghentikan notifikasi suara otomatis selama jam-jam istirahat.
*   **Jam Sunyi Mulai / Selesai (HH:MM)**: Tulis waktu mulai dan selesai jam sunyi menggunakan format 24 jam (contoh: mulai `22:00` dan selesai `06:00`).
*   **Lewati Verifikasi SSL**: Centang jika Anda menemui kendala koneksi SSL atau sertifikat tidak valid dari portal berita (disarankan tidak dicentang kecuali darurat).
*   **Jumlah Berita Awal yang Ditampilkan**: Memilih batas awal berita yang tampil di daftar (20, 50, atau 100 berita) untuk mempercepat loading dialog.
*   **Batas Penyimpanan Cache (Hari)**: Menentukan berapa lama artikel yang sudah diunduh tetap disimpan secara lokal (1 hingga 30 hari). Berita yang lebih lama akan dihapus otomatis pada saat NVDA dimulai untuk menghemat ruang disk.
*   **Hapus Semua Cache Berita**: Klik tombol ini untuk mengosongkan seluruh database cache berita secara manual. Dialog konfirmasi akan muncul sebelum penghapusan.

---

## Riwayat Versi

Riwayat lengkap ada di file CHANGELOG.md di repositori https://github.com/InfiArtt/nusa-news-id.

---

## Kontributor
*   **Rexya Muhamad Rizki** (Pengembang Utama / Lead Developer)
*   **NusaNews ID Team**
*   Dibuat khusus untuk komunitas tunanetra dan pengguna pembaca layar di Indonesia.
