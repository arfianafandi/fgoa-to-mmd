================================================================================
             PANDUAN ALAT KONVERSI MODEL FGO ARCADE KE MMD (.PMX)
================================================================================

Folder ini berisi tool otomatis untuk memperbaiki dan mengonversi model-model
hasil dump game Fate/Grand Order Arcade (FGOA) menjadi model MMD (.pmx) yang
lengkap dengan tekstur, transparansi alfa, tulang hierarki, dan fisika kain.

--------------------------------------------------------------------------------
1. DAFTAR FILE TOOLS
--------------------------------------------------------------------------------
- Run_GUI.bat
  -> Menjalankan aplikasi tampilan visual (GUI) yang mudah digunakan.

- Convert_to_MMD (Drag & Drop).bat
  -> Cukup seret (drag and drop) folder model atau file .pmx ke file bat ini!

- Batch_Convert_ALL.bat
  -> 1x Klik untuk mengonversi seluruh model senjata dan karakter yang ada
     di dalam folder E:\FGO\FGOA secara otomatis.

- fgoa_to_mmd.py
  -> Script mesin konversi utama berbasis Python.

- pmx_lib.py
  -> Library pembaca dan penulis format biner PMX 2.0.


--------------------------------------------------------------------------------
2. CARA MENGGUNAKAN TOOL
--------------------------------------------------------------------------------

METODE A: DRAG & DROP (Paling Praktis)
1. Buka folder "E:\FGO\FGOA" di File Explorer.
2. Ambil folder senjata/model yang ingin kamu ubah (misal: "WP Saber" atau "WP Nero").
3. Tarik (Drag) folder tersebut lalu Lepas (Drop) tepat di atas file:
   "Convert_to_MMD (Drag & Drop).bat"
4. Tunggu beberapa detik hingga proses selesai. Selesai!

METODE B: MENGGUNAKAN APLIKASI GUI
1. Dobel klik file "Run_GUI.bat".
2. Jendela aplikasi akan terbuka.
3. Klik tombol "Pilih Folder" dan pilih folder model yang ingin dikonversi.
4. Klik tombol "▶ Convert Target yang Dipilih".
5. Log proses akan berjalan di layar dan memberi tahu saat selesai.

METODE C: BATCH CONVERT SEMUA MODEL SEKALIGUS
1. Dobel klik "Batch_Convert_ALL.bat".
2. Ketik 'Y' lalu tekan Enter.
3. Tool akan otomatis memindai seluruh folder di E:\FGO\FGOA dan mengonversi
   semua model senjata dan karakter yang belum dikonversi.


--------------------------------------------------------------------------------
3. APA SAJA YANG DIPERBAIKI SECARA OTOMATIS OLEH TOOL INI?
--------------------------------------------------------------------------------
1. Tekstur Hilang / Putih:
   - File PMX mentah sering tidak menyertakan ekstensi file (.png).
   - Tool otomatis memetakan kembali nama tekstur ke file PNG aslinya.

2. Tekstur Tembus Pandang (Alpha = 0 Bug):
   - Tekstur dump mentah sering memiliki channel alpha = 0 (membuat model 100% tembus pandang).
   - Tool menggabungkan alpha mask asli (_a_*.png) untuk bulu, rumbai, dan ornamen transparan.
   - Tekstur pakaian/pedang/baja dibuat solid opaque (alpha = 255) agar tidak hilang.

3. Tulang Lepas / Terputus:
   - Tulang ornamen dan kain (misal: 'body_m') yang aslinya terputus (parent = -1)
     otomatis disambungkan ke tulang tiang/pedang ('body').
   - Menambahkan tulang standar MMD:
     * '全ての親' (Master Root di titik 0,0,0)
     * 'センター' (Center Bone)

4. Kain Tembus Pandang dari Belakang:
   - Mengaktifkan fitur Double-sided rendering (両面描画) agar kain bendera,
     pita, dan bulu terlihat dari kedua sisi saat berputar/berkibar.

5. Refleksi Logam:
   - Otomatis membuatkan file sphere map (.spa) dari tekstur envmap.


--------------------------------------------------------------------------------
4. MODEL HASIL KONVERSI YANG AKAN DIDAPATKAN DI FOLDER:
--------------------------------------------------------------------------------
Setiap folder yang dikonversi akan memiliki:

1. [NamaModel]_Stand.pmx (Rekomendasi Utama)
   - Model berdiri tegak lurus di atas lantai (sumbu Y ke atas, dasar di Y = 0).
   - Posisi pegangan tangan ('持ち手') berada di ketinggian tangan normal (~1.0m - 1.6m).
   - Sangat cocok untuk diletakkan di panggung, dipegang karakter, atau dibuat animasi.

2. [NamaModel]_Equip.pmx
   - Mempertahankan koordinat genggaman tangan asli game (Z-axis).
   - Sangat cocok digunakan untuk fitur "Outside Parent" (外部親登録) di MMD
     langsung ke tulang tangan karakter ('右手' atau '左手') dengan offset 0.

3. [NamaModel]_Physics.pmx (Jika model memiliki kain/bendera/tali)
   - Dilengkapi Rigid Body (剛体) dan Spring Joint (ジョイント) MMD.
   - Kain atau pita akan bergoyang dan berkibar otomatis mengikuti gerakan panggung MMD.

4. [Nama_Objout].pmx
   - File mentah asli juga ikut diperbarui langsung agar bisa dibuka di MMD
     (file aslinya telah dicadangkan otomatis sebagai .pmx.bak).
