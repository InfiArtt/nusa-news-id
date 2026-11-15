# NusaNewsID

NusaNewsID membacakan berita dari situs berita Indonesia di NVDA. Add-on ini memeriksa berita baru di latar belakang, mengumumkannya, dan menampilkan isi artikel di jendela yang mudah dibaca, jadi Anda tidak perlu membuka browser yang penuh iklan.

Bahasa add-on mengikuti bahasa NVDA. Panduan ini memakai nama tombol dan pesan dalam bahasa Indonesia.

## Kebutuhan

- NVDA 2026.1 atau yang lebih baru.
- Koneksi internet.

## Sumber dan kategori

Ada sepuluh kategori: Nasional, Internasional, Teknologi, Politik, Ekonomi, Olahraga, Entertainment, Disabilitas, Artikel InfiArtt, dan Pusat Pengetahuan. Tidak semua sumber punya semua kategori, karena add-on hanya mengambil bagian yang masih diperbarui oleh situsnya.

- Antara, Kompas, Liputan6, Merdeka, dan CNN Indonesia: semua kategori.
- Detik: semua kategori kecuali Politik.
- Republika: Nasional, Internasional, Teknologi, Ekonomi, Olahraga, dan Disabilitas.
- WinPoin, berita Windows dan Microsoft: Teknologi.
- InfiArtt, organisasi yang membuat add-on ini: Artikel InfiArtt (dari infiartt.com/posts) dan Pusat Pengetahuan (panduan dari infiartt.com/kb). InfiArtt selalu diperiksa dan tidak bisa dimatikan, jadi artikel dan panduan barunya selalu muncul di daftar berita. Artikel khusus anggota InfiArtt menampilkan ringkasannya saja; bukalah di browser dan masuk untuk membacanya.

Berita diambil dari feed RSS situs jika feed-nya terus diperbarui, dan dari halaman kategori jika tidak. Setiap berita tetap di kategori tempat ia tercantum. Berita yang lebih tua dari batas penyimpanan tidak diambil.

Kategori Disabilitas berisi berita tentang disabilitas dan penyandang disabilitas. Untuk sumber yang tidak punya kanal khusus, add-on mengambil halaman tag disabilitas dan hanya menyimpan berita yang judul atau ringkasannya memuat kata seperti disabilitas, difabel, tunanetra, Tuli, atau kursi roda. Kata dicocokkan sebagai kata utuh.

## Membuka daftar berita

Tekan NVDA+Shift+garis miring dari mana saja. Daftar berita terbuka dengan fokus di berita terbaru. Tombol ini bisa diganti di menu NVDA, Pilihan, Input Gestures, kategori NusaNewsID.

Jika daftar berita sudah terbuka, tombol yang sama memindahkan fokus kembali ke daftar itu.

## Daftar berita

Setiap berita dibacakan dengan urutan yang sama: judul, lalu sumber, kategori, dan waktu. Contohnya:

"Sapaan Prabowo ke Jenderal Suyudi. Detik, Nasional, 14 menit lalu. Belum dibaca."

- Kata "Breaking." ada di depan judul hanya untuk berita breaking.
- Kata "Belum dibaca." ada di akhir hanya untuk berita yang belum Anda buka atau tandai dibaca.
- Waktu dibacakan "baru saja", "14 menit lalu", atau "3 jam lalu" untuk berita hari ini, lalu berupa tanggal dan jam, misalnya "13 November 2026 pukul 20.00".
- Jika situs tidak mencantumkan waktu terbit, add-on memakai waktu saat pertama kali menemukan berita itu.

Berita terbaru ada di atas. Daftar menampilkan 50 berita sekaligus, dan jumlah ini bisa diubah di pengaturan. Item terakhir berbunyi misalnya "Muat 50 berita berikutnya". Tekan Enter di item itu untuk menampilkan berita berikutnya.

Tekan Enter pada berita untuk membacanya.

Di atas daftar ada filter dan pilihan berikut:

- Sumber (Alt+S): tampilkan berita dari satu sumber saja, atau Semua.
- Kategori (Alt+K): tampilkan satu kategori saja, atau Semua.
- Hanya yang belum dibaca (Alt+B): sembunyikan berita yang sudah dibaca.

Di bawah daftar ada tombol berikut:

- Salin link (Alt+L): menyalin alamat web berita yang dipilih.
- Tandai dibaca (Alt+D): menandai berita yang dipilih sudah dibaca.
- Tandai semua dibaca (Alt+M): menandai semua berita tersimpan sudah dibaca.
- Segarkan (Alt+G): memeriksa berita baru sekarang. NVDA mengucapkan "Memeriksa berita baru...", lalu misalnya "Selesai, 3 berita baru." atau "Selesai, tidak ada berita baru."
- Donasi (Alt+O): informasi donasi untuk pengembangan add-on.
- Tutup (Alt+T atau Escape).

Jika daftar kosong, misalnya karena filter tidak cocok dengan berita apa pun, daftar berisi satu baris yang menjelaskannya.

Saat berita baru masuk ketika daftar terbuka, daftar diperbarui dan berita yang sedang Anda pilih tetap terpilih.

## Membaca berita

Pembaca membuka berita sebagai halaman yang dibaca NVDA dalam mode browse, dengan judul berita sebagai judul jendela. Gunakan tombol panah untuk membaca, H untuk berpindah per judul bagian, L untuk daftar, dan K untuk tautan. Isi berita ditandai berbahasa Indonesia, jadi jika pengaturan pergantian bahasa otomatis di NVDA aktif, NVDA membacanya dengan suara bahasa Indonesia.

Bagian atas halaman berisi:

1. Judul berita, sebagai heading level 1.
2. Sumber dan kategori, misalnya "Detik, kategori Nasional".
3. Waktu terbit, misalnya "Terbit 15 November 2026 pukul 06.09". Jika situs tidak mencantumkannya, baris ini berbunyi "Ditemukan ..." dengan waktu add-on pertama kali menemukan berita itu.
4. Alamat web berita.

Setelah itu isi berita, lengkap dengan judul bagian, daftar, kutipan, dan tautan dari artikel aslinya. Iklan, kotak "baca juga", kotak samping, dan catatan hak cipta dibuang. Gambar hanya tampil jika punya keterangan. Tautan dibuka di browser.

Saat pertama kali dibuka, isi berita diunduh dulu. NVDA mengucapkan "Isi berita sudah dimuat." setelah selesai. Isi yang sudah diunduh disimpan, jadi bisa dibaca lagi tanpa internet selama berita itu masih tersimpan. Membuka berita juga menandainya sudah dibaca.

Untuk pengguna low vision:

- Control+tambah memperbesar teks, Control+kurang memperkecilnya, dan Control+0 kembali ke 100 persen. Ukurannya dari 100 sampai 400 persen, dan NVDA menyebutnya, misalnya "Ukuran teks 150 persen". Ukuran ini diingat untuk berita berikutnya.
- Warna halaman mengikuti warna Windows, termasuk tema kontras. Jarak baris lega, dan baris paling panjang sekitar 70 karakter, jadi teks besar tetap terlipat rapi tanpa perlu menggulir ke samping.
- Tombol yang sedang difokus diberi garis tepi yang jelas.

Tombol di akhir halaman, yang juga bisa dipakai dari mana saja di halaman dengan tombol pintasnya:

- Buka di browser (Alt+B): membuka berita di situs aslinya.
- Salin link (Alt+L): menyalin alamat web berita.
- Salin berita (Alt+S): menyalin judul dan isi berita, tanpa baris keterangan.
- Tutup (Alt+T atau Escape): kembali ke daftar berita.

Jika Windows tidak bisa menampilkan halaman web, pembaca memakai kotak teks biasa dengan isi yang sama.

## Pemberitahuan berita baru

Add-on memeriksa berita baru setiap 5 menit, dan interval ini bisa diubah di pengaturan. Pemeriksaan pertama dimulai beberapa detik setelah NVDA berjalan.

Ada dua cara pemberitahuan:

- Ringkasan jumlah berita baru, bawaan: satu pesan, misalnya "NusaNews: 5 berita baru. Tekan NVDA+shift+/ untuk membuka." Pesan ini menyebut tombol yang Anda pakai untuk membuka daftar berita, termasuk jika Anda menggantinya di Input Gestures.
- Judul setiap berita baru: judul semua berita baru dalam satu pesan, misalnya "Berita baru dari Detik: ...". Jika ada lebih dari 5 berita baru, NVDA memakai ringkasan.

Semua pemberitahuan juga tampil di layar braille.

Berita breaking adalah berita tentang bencana dan keadaan darurat. Add-on mengenalinya dari kata utuh di judul: gempa, tsunami, erupsi, meletus, banjir bandang, longsor, kebakaran hutan, bencana, darurat, evakuasi, peringatan dini, bom, teroris, dan "breaking news".

Pemeriksaan pertama setelah add-on dipasang, atau setelah semua berita tersimpan dihapus, tidak mengumumkan berita satu per satu. Berita itu disimpan sebagai sudah dibaca, lalu NVDA mengucapkan satu pesan, misalnya "NusaNews: 450 berita dimuat."

## Jam sunyi

Selama jam sunyi, add-on tidak mengumumkan berita baru dan tidak membunyikan nada. Berita tetap disimpan dan bisa dibaca di daftar berita. Jika pilihan "Umumkan berita breaking juga saat jam sunyi" dicentang, berita breaking tetap diumumkan.

Jam sunyi boleh melewati tengah malam, misalnya mulai 22:00 dan selesai 06:00.

## Pengaturan

Buka menu NVDA, Pilihan, Settings, lalu pilih kategori NusaNewsID. Mulai NVDA 2026.3, pengaturan ini sama di semua profil konfigurasi.

- Sumber berita yang dipantau: daftar kotak centang. Pilih setidaknya satu sumber. InfiArtt tidak ada di daftar ini karena selalu diperiksa.
- Periksa berita baru setiap (menit): 2, 5, 10, 15, 30, 60, atau 120 menit.
- Grup Notifikasi:
  - Cara memberi tahu berita baru: Ringkasan jumlah berita baru, atau Judul setiap berita baru.
  - Bunyikan nada saat ada berita baru.
  - Umumkan berita breaking juga saat jam sunyi.
- Grup Jam sunyi:
  - Aktifkan jam sunyi.
  - Mulai dan Selesai: jam dan menit, misalnya 22:00 dan 06:00. Jika formatnya salah, NVDA memberi tahu kolom mana yang perlu diperbaiki.
- Jumlah berita yang ditampilkan sekaligus: 20, 50, atau 100.
- Ukuran teks pembaca (persen): 100 sampai 400 persen. Control+tambah dan Control+kurang di pembaca juga mengubahnya.
- Grup Penyimpanan:
  - Lama penyimpanan berita (hari): 1 sampai 30 hari. Berita yang lebih lama dihapus setiap kali pemeriksaan selesai.
  - Hapus semua berita tersimpan: menghapus semua berita dan isi artikel yang tersimpan, setelah Anda menekan Hapus di dialog konfirmasi. Tindakan ini tidak bisa dibatalkan.
- Lewati pemeriksaan sertifikat keamanan: pakai hanya jika semua koneksi selalu gagal karena masalah sertifikat di komputer Anda. Pilihan ini membuat koneksi tidak aman.
- Dukungan dan donasi.

## Data yang disimpan

Berita disimpan di folder pengaturan NVDA, dalam folder nusaNewsID. File nusaNewsCache.json berisi judul, sumber, kategori, waktu, dan status dibaca setiap berita. Folder articles berisi isi artikel yang sudah Anda buka.

Add-on hanya menghubungi situs berita yang Anda pilih. Add-on tidak mengirim data pribadi ke mana pun.

## Jika ada masalah

- Tidak ada berita sama sekali: periksa koneksi internet, lalu tekan Segarkan di daftar berita.
- Satu sumber tidak pernah punya berita baru: situs itu mungkin mengubah tampilannya. Laporkan di halaman issue repositori di bawah.
- Isi berita gagal diunduh: tekan Buka di browser untuk membacanya di situs aslinya.

## Riwayat perubahan

Riwayat lengkap ada di file CHANGELOG.md di repositori https://github.com/InfiArtt/nusa-news-id.

## Pembuat dan lisensi

NusaNewsID dibuat oleh Rexya Muhamad Rizki dan dikembangkan bersama InfiArtt. Laporan masalah dan usulan bisa dikirim lewat https://github.com/InfiArtt/nusa-news-id/issues.

Add-on ini dirilis dengan lisensi GNU General Public License versi 2 atau lebih baru.
