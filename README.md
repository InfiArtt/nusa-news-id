# NusaNewsID

Add-on NVDA untuk mengikuti berita Indonesia dari Antara, Kompas, Detik, Republika, Liputan6, Merdeka, CNN Indonesia, dan WinPoin, serta artikel dan pusat pengetahuan InfiArtt. Add-on memeriksa berita baru di latar belakang, mengumumkannya dengan NVDA, diam selama jam sunyi, dan menampilkan isi artikel di jendela yang mudah dibaca tanpa membuka browser.

Panduan pengguna ada di `addon/doc/id/readme.md` (bahasa Indonesia) dan `addon/doc/en/readme.md` (bahasa Inggris). Panduan yang sama bisa dibuka dari Pengelola Add-on NVDA setelah add-on dipasang.

## Versi NVDA

- Versi minimum: NVDA 2026.1.
- Terakhir diuji: NVDA 2026.3.1.

## Membangun add-on

1. Pasang Python 3.13 dan gettext.
2. Jalankan `pip install --group build --group test ruff`.
3. Jalankan `scons`. Hasilnya `nusaNewsID-<versi>.nvda-addon`.

Uji otomatis dijalankan dengan `python -m pytest`, dan pemeriksaan gaya kode dengan `ruff check .` serta `ruff format --check .`.

## Riwayat perubahan

Riwayat lengkap ada di `CHANGELOG.md`.

## Lisensi

GNU General Public License versi 2 atau lebih baru. Lihat `LICENSE`.
