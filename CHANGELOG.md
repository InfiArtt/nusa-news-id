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

### Dihapus

- Tempo dihapus dari pengaturan, karena situs dan artikelnya menolak akses dari add-on dengan error 403. Tempo yang masih tercentang di pengaturan lama diabaikan.

### Diubah

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
