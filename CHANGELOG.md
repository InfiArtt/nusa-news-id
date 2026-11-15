# Riwayat perubahan NusaNewsID

Format mengikuti Keep a Changelog. Ringkasan berbahasa Inggris untuk versi yang sedang dikerjakan ada di `addon_changelog` di `buildVars.py`, dan ditampilkan di Add-on Store.

## [1.1.0] - belum dirilis

### Diperbaiki

- Merdeka kembali berfungsi. Sebelumnya setiap kategori hanya berisi tautan footer seperti "Pedoman Media Siber", karena alamat artikel Merdeka berubah dari akhiran .html menjadi bentuk `merdeka.com/peristiwa/read/8335388/judul-berita`.
- Antara kembali berfungsi di dalam NVDA. Sebelumnya setiap permintaan gagal dengan "CERTIFICATE_VERIFY_FAILED, unable to get local issuer certificate", karena akar sertifikat Antara belum ada di penyimpanan sertifikat Windows. Sertifikat sekarang diperiksa dengan kumpulan sertifikat certifi yang dibawa NVDA, ditambah sertifikat Windows.
- Error sertifikat tidak lagi dicoba ulang tiga kali. Sebelumnya Antara membuang sekitar 48 detik di setiap putaran.
- Tombol Segarkan dan tombol OK di pengaturan tidak lagi membuat thread pengambil berita kedua, jadi berita tidak lagi diumumkan dua kali. Setelah Segarkan, NVDA mengucapkan jumlah berita baru yang ditemukan.
- Menutup NVDA atau memuat ulang add-on tidak lagi menunggu putaran pengambilan berita selesai. Pengambilan berhenti di antara dua permintaan, dan jeda percobaan ulang bisa dihentikan.
- Di layar aman, misalnya layar masuk Windows, dialog pembaca berita tidak lagi terbuka, dan NVDA tidak lagi mencatat error AttributeError saat add-on ditutup.
- Pengaturan dibaca di thread utama NVDA, tidak lagi dari thread latar.

- Judul berita bersih di semua sumber. Sisa teks seperti jam ("18:13Jangan Biarkan ..."), nama kanal ("Nasional - , 03:33 ...", "... Politik Nasional", "detikJatimJumat, 12:00 WIB ..."), dan kata "Headline" tidak lagi ikut terbaca. Judul diambil dari judul utama kartu berita, bukan dari seluruh teks tautan.
- Kategori berita akurat. Tautan dari kotak samping (misalnya "Terkini" di Antara), kotak "Populer", menu, footer, dan kanal lain di halaman yang sama tidak lagi masuk ke kategori yang sedang diambil. Contohnya, berita Cek Fakta tidak lagi masuk Teknologi Liputan6, dan berita sepak bola tidak lagi masuk Nasional Antara.
- Tanggal terbit dibaca dengan benar dan disimpan dalam satu format waktu standar. Waktu relatif seperti "10 jam lalu" dihitung dari jam pengambilan. CNN Indonesia dan Kompas memakai waktu yang tercantum di alamat artikel. Tanggal Republika tidak lagi tertukar ke artikel lain.
- Berita yang lebih tua dari batas cache tidak lagi diambil, jadi berita Republika dari 2023 dan 2024 tidak lagi diumumkan sebagai berita baru.
- Tanda breaking hanya untuk bencana dan keadaan darurat: gempa, tsunami, erupsi, meletus, banjir bandang, longsor, kebakaran hutan, bencana, darurat, evakuasi, peringatan dini, bom, teroris, dan "breaking news". Kata "presiden", "waspada", "urgent", dan "breaking" dihapus. Dalam uji 506 judul, 21 dari 29 tanda breaking sebelumnya hanya karena kata "presiden".
- Kata kunci breaking dan Disabilitas dicocokkan sebagai kata utuh. "tuli" tidak lagi cocok dengan "menulis". Kata yang punya arti lain juga dihapus dari daftar Disabilitas, yaitu "lumpuh", "cacat", "buta", "bisu", "inklusi", "inklusif", "aksesibilitas", "aksesibel", "gangguan jiwa", "panti sosial", dan "rehabilitasi sosial".

### Diubah

- Semua provider sekarang memakai satu kelas dasar yang sama. Setiap provider hanya berisi data: alamat RSS dan halaman per kategori, pola alamat artikel, dan bagian alamat yang menandai kategori.
- Berita diambil dari RSS jika ada dan segar, yaitu CNN Indonesia, Detik, Liputan6, Republika, sebagian Antara, dan WinPoin. Kompas, Merdeka, dan kategori yang RSS-nya basi memakai halaman kategori. Jika RSS gagal atau berisi kurang dari 5 berita terbaru, berita dari halaman kategori ditambahkan, tanpa duplikat.
- Olahraga Merdeka sekarang diambil dari kanal sepakbola dan sport, karena kanal bolasport dan olahraga sudah tidak diperbarui. Olahraga Republika diambil dari RSS sport.
- Ada skrip `tools/checkProviders.py` untuk mengecek semua sumber dan kategori langsung ke situs, di luar NVDA.

### Dihapus

- Tempo dihapus dari pengaturan, karena situs dan artikelnya menolak akses dari add-on dengan error 403.
- MacPoin dihapus, karena artikel terakhirnya terbit 8 Maret 2024.
- Tempo dan MacPoin yang masih tercentang di pengaturan lama diabaikan.
- Kategori yang sudah tidak diperbarui oleh situsnya: Politik di Detik (Detik tidak punya kanal politik dan RSS pemilunya basi), serta Politik dan Entertainment di Republika (terakhir diperbarui 2024 dan 2023).

- Proyek dipindahkan ke repositori InfiArtt/nusa-news-id dan memakai template add-on NV Access. Manifest sekarang dibuat dari `buildVars.py`.
- Versi NVDA terakhir yang diuji: 2026.3.1.
- Lisensi: GNU General Public License versi 2 atau lebih baru.

## [1.0.2]

### Ditambahkan

- Tombol Salin Link (Alt+L) di dialog utama dan di mode membaca offline.
- Jendela sambutan dan informasi donasi saat add-on dipasang.
- Informasi donasi di panel pengaturan dan di dialog utama.

### Diperbaiki

- Alamat kategori Politik untuk Detik dan Merdeka.
- Kategori Politik yang kosong pada Detik dan Antara, dengan menyimpan beberapa kategori untuk satu berita di cache.

### Dihapus

- Parser RSS (`rssProvider.py`) dan sisa kode yang tidak dipakai.

## [1.0.1]

### Diperbaiki

- Kategori Olahraga Merdeka, dengan alamat baru ke bolasport.
- Tanggal yang hilang di beberapa provider, dengan membaca tanggal dari judul berita.
- Teks "Berita Terkait" yang ikut terbaca di mode membaca pada Merdeka.

### Ditambahkan

- Dukungan halaman yang dikompresi Gzip.

## [1.0.0]

### Ditambahkan

- Rilis pertama NusaNewsID dengan 10 portal berita Indonesia.
- Mode membaca offline, dengan dukungan artikel beberapa halaman untuk Detik dan Kompas.
- Penyaringan berita isu disabilitas dengan kata kunci.
- Jam sunyi, batas awal tampilan, dan item "Muat Lebih Banyak".
- Cache berbasis JSON.
- Tombol pintas Alt+D, Alt+M, Alt+S, Alt+T, dan Alt+B.
