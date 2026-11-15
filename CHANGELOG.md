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
- Menutup pembaca artikel tidak lagi membuat NVDA membacakan baris berita dua kali. Baris itu diperbarui di tempat sebelum fokus kembali ke daftar.
- Tanggal yang tersimpan sebagai teks oleh versi lama, misalnya "10 jam lalu", dibaca ulang dari waktu berita disimpan. Teks yang ternyata kalimat dari isi berita, misalnya "... 29 Desember 2026", tidak lagi dianggap waktu terbit, sehingga berita lama tidak lagi terbaca "baru saja" dan naik ke atas daftar. Tanggal yang jatuh di masa depan juga diabaikan saat berita diambil.
- Berita yang lebih tua dari batas cache tidak lagi diambil, jadi berita Republika dari 2023 dan 2024 tidak lagi diumumkan sebagai berita baru.
- Tanda breaking hanya untuk bencana dan keadaan darurat: gempa, tsunami, erupsi, meletus, banjir bandang, longsor, kebakaran hutan, bencana, darurat, evakuasi, peringatan dini, bom, teroris, dan "breaking news". Kata "presiden", "waspada", "urgent", dan "breaking" dihapus. Dalam uji 506 judul, 21 dari 29 tanda breaking sebelumnya hanya karena kata "presiden".
- Kata kunci breaking dan Disabilitas dicocokkan sebagai kata utuh. "tuli" tidak lagi cocok dengan "menulis". Kata yang punya arti lain juga dihapus dari daftar Disabilitas, yaitu "lumpuh", "cacat", "buta", "bisu", "inklusi", "inklusif", "aksesibilitas", "aksesibel", "gangguan jiwa", "panti sosial", dan "rehabilitasi sosial".

### Diubah

- Teks antarmuka sekarang ditulis dalam bahasa Inggris sebagai teks sumber, sesuai standar NVDA, dengan terjemahan Indonesia di `addon/locale/id/LC_MESSAGES/nvda.po`. NVDA memakai bahasa Indonesia jika bahasa NVDA bahasa Indonesia, dan bahasa Inggris untuk bahasa lain. Semua teks punya komentar `Translators:` untuk penerjemah. Ringkasan, deskripsi, dan riwayat perubahan di manifest juga diterjemahkan. Nama kategori tetap disimpan dalam bahasa Indonesia di cache, dan hanya tampilannya yang diterjemahkan.
- Tombol pintas di bahasa Inggris dan Indonesia dipilih supaya tidak ada yang sama dalam satu jendela. Di bahasa Indonesia tombolnya sama seperti sebelumnya, misalnya Segarkan Alt+G. Di bahasa Inggris Refresh memakai Alt+R.
- Teks antarmuka bahasa Inggris dan Indonesia ditulis ulang supaya lebih wajar dan langsung, misalnya teks donasi dan jendela sambutan saat pemasangan.
- Kategori add-on di Input Gestures sekarang bernama "NusaNewsID".
- Panduan pengguna bahasa Indonesia dan Inggris ditulis ulang sesuai perilaku versi ini: sumber dan kategori per situs, format baca, tombol pintas, pemberitahuan, jam sunyi, pengaturan, data yang disimpan, dan langkah jika ada masalah. Nama menu NVDA di panduan Indonesia mengikuti terjemahan NVDA, misalnya Pilihan, Settings, dan Input Gestures. Riwayat versi dipindahkan ke CHANGELOG.md.
- Cache disimpan di memori. Perubahan ditulis ke disk sekitar 2 detik setelah perubahan terakhir oleh thread latar, dan sekali lagi saat NVDA ditutup, dalam JSON ringkas. Menandai berita dibaca, membuka artikel, atau memuat daftar tidak lagi membaca dan menulis ulang seluruh file di thread utama. Format file dan nama kolomnya sama, jadi cache lama langsung terbaca. Pada cache uji, ukurannya turun dari 3,3 MB menjadi 2,3 MB.
- Isi artikel disimpan di file terpisah per artikel di folder `articles`, dan hanya dibaca saat artikel dibuka. Isi artikel yang tersimpan di dalam cache versi lama dipindahkan otomatis.
- Berita lama dihapus di setiap putaran pengambilan, tidak hanya saat NVDA mulai. Isi artikelnya ikut dihapus.
- Batas 500 berita di daftar dihapus, jadi "Muat ... berita berikutnya" bisa terus sampai semua berita tampil.
- Pengisian pertama, yaitu setelah add-on dipasang atau setelah berita tersimpan dihapus, berjalan tanpa nada dan tanpa pengumuman per berita. Berita dari pengisian pertama langsung ditandai dibaca, lalu NVDA mengucapkan satu pesan, misalnya "NusaNews: 450 berita dimuat."
- Saat versi 1.1.0 pertama kali berjalan, semua berita dari versi lama ditandai dibaca sekali saja, tanpa dihapus. Dengan begitu "Belum dibaca" hanya untuk berita yang masuk sesudahnya. Pada uji, ada 5.942 berita yang semuanya berstatus belum dibaca sebelumnya.
- Mulai NVDA 2026.3, pengaturan NusaNews didaftarkan dengan `config.configSections.registerSection` sebagai bagian khusus konfigurasi utama (base only), saat add-on dipasang. Jadi pengaturannya sama di semua profil konfigurasi. Saat add-on dihapus, pendaftaran itu ikut dihapus. Di NVDA 2026.1 dan 2026.2, cara lama tetap dipakai.
- `config.conf.save()` tidak lagi dipanggil add-on; NVDA menyimpan sendiri saat tombol OK ditekan.
- Panel pengaturan ditata ulang dengan `guiHelper` NVDA. Setiap kontrol punya label yang terhubung, dan pilihan dikelompokkan ke grup Notifikasi, Jam sunyi, dan Penyimpanan, yang namanya diumumkan NVDA. Sumber berita sekarang berupa daftar centang. Kotak jam sunyi hanya aktif jika jam sunyi dicentang, dan jam harus berformat jam:menit, misalnya 22:00. Kalau salah, NVDA menyebut kolom mana yang salah. Minimal satu sumber harus dipilih. Tombol pintas semua kontrol berbeda satu sama lain.
- Konfirmasi Hapus semua berita tersimpan memakai `gui.message.MessageDialog` milik NVDA, dengan tombol Hapus dan Batal.
- Dialog daftar berita sekarang memakai jendela NVDA sebagai induk, dan muncul di depan saat dibuka. Kalau sudah terbuka, fokus langsung ke daftar. Daftar berita punya label "Daftar berita. Tekan Enter untuk membaca". Filter berlabel "Sumber" (Alt+S) dan "Kategori" (Alt+K). Tombol Segarkan pindah ke Alt+G karena Alt+S dipakai filter Sumber.
- Saat berita baru masuk, berita yang sedang dipilih tetap terpilih. Sebelumnya pilihan pindah ke berita lain karena urutan bergeser.
- Pembaca artikel memakai judul berita sebagai judul jendela. Kotak isi artikel berlabel "Isi berita". Artikel yang selesai diunduh setelah pembaca ditutup tetap disimpan.
- Satu format baca untuk semua tempat, dibuat oleh satu modul (`formatting.py`):
  - Daftar berita: "Judul. Sumber, Kategori, waktu." lalu "Belum dibaca." di akhir untuk berita yang belum dibaca. Kata "Breaking." di depan judul hanya untuk berita breaking. Sebelumnya: "[Baru] [BREAKING] [Detik] judul", tanpa kategori dan waktu.
  - Item terakhir daftar: "Muat 50 berita berikutnya", dengan angka sebanyak berita yang akan dimuat. Sebelumnya: "-- Muat Lebih Banyak --".
  - Notifikasi satu berita: "Berita baru dari Detik: judul." atau "Breaking dari Antara: judul." Beberapa berita dalam mode langsung digabung menjadi satu pesan, supaya semuanya tampil di layar braille.
  - Ringkasan: "NusaNews: 5 berita baru. Tekan NVDA+shift+/ untuk membuka." Nama tombol diambil dari NVDA, termasuk perubahan di Input Gestures. Jika tombolnya dihapus, pesan menyarankan menetapkannya di Input Gestures.
  - Pembaca artikel: judul, lalu "Detik, kategori Nasional", lalu "Terbit 15 November 2026 pukul 06.09", lalu link, masing-masing di baris sendiri. Untuk berita tanpa waktu terbit dari situsnya, baris ketiga berbunyi "Ditemukan ..." dengan waktu add-on pertama kali menemukannya. Sebelumnya ada garis vertikal dan garis 60 tanda minus.
  - Tombol Salin berita hanya menyalin judul dan isi berita.
- Waktu ditampilkan "baru saja", "14 menit lalu", atau "3 jam lalu" untuk 24 jam terakhir, dan "13 November 2026 pukul 20.00" untuk yang lebih lama, dalam zona waktu komputer.
- Daftar diurutkan menurut waktu terbit, yang terbaru di atas. Berita tanpa waktu terbit memakai waktu pertama kali ditemukan.
- Tanda breaking pada berita yang tersimpan dari versi lama dihitung ulang dengan aturan baru.
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
