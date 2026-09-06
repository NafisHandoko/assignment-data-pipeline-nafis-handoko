# Data Pipeline: Automobile Dataset

Pipeline ETL sederhana menggunakan Python + Pandas untuk mengolah dataset otomotif mentah hingga siap dipakai untuk analisis/pemodelan: **Load → Inspection → Cleaning → Transformation → Save**.

Tugas ini merupakan individual assignment **Data Engineering: Pipeline & Preparation** (Rework Academy, Sesi 3).

---

## 📊 Deskripsi Dataset

Dataset berisi **data otomotif** berukuran **205 baris × 30 kolom** — spesifikasi mobil (engine-size, horsepower, curb-weight, body-style, dll.) beserta atribut transaksi (`transaction_date`, `price`).

**Sumber dataset:** disediakan mentor melalui [s.id/dataset-sesi-3](https://s.id/dataset-sesi-3) (`Dataset_Sesi_3.zip`), terdiri dari:

| File | Peran |
|---|---|
| `automobileEDA_dirty_training.csv` | **Dataset utama** — input pipeline (yang diproses) |
| `automobileEDA.csv` | Dataset original — hanya referensi |
| `automobile_processed.csv` | Clean dataset — hanya pembanding hasil |

Dataset hasil akhir **100% dihasilkan oleh `src/pipeline.py`**, bukan disalin dari clean dataset referensi.

---

## 📁 Struktur Folder

```
assignment-data-pipeline-nafis-handoko/
├── data/
│   ├── raw/
│   │   ├── automobileEDA_dirty_training.csv   # dataset mentah (tidak pernah ditimpa)
│   │   ├── cleaned.csv                        # hasil antara (cleaning) dari notebook
│   │   └── normalized.csv                     # hasil antara (transformasi) dari notebook
│   └── processed/
│       └── automobileEDA_processed.csv        # OUTPUT akhir pipeline
├── src/
│   ├── pipeline.py                            # script pipeline (dapat dijalankan ulang)
│   └── pipeline.ipynb                         # notebook eksplorasi/analisis
├── README.md
└── requirements.txt
```

---

## 🔍 Kondisi Awal Dataset

Hasil pemeriksaan awal terhadap `data/raw/automobileEDA_dirty_training.csv`:

**Catatan kecil:** `df.shape` menunjukkan `205, 30` — padahal saat dicek manual file-nya terlihat 206 baris. Penyebabnya baris pertama dipakai Pandas sebagai nama kolom, sehingga tidak ikut terhitung sebagai baris data.

**Ukuran awal:** 205 baris × 30 kolom.

**Missing values** — 17 sel kosong tersebar di 7 kolom:

| Kolom | Jumlah NaN |
|---|---|
| `stroke` | 4 |
| `horsepower` | 3 |
| `price` | 3 |
| `transaction_date` | 2 |
| `make` | 2 |
| `num-of-doors` | 2 |
| `horsepower-binned` | 1 |

> Tips dari proses: dengan 30 kolom, `df.isna().sum()` rawan ada kolom yang terlewat saat dibaca. Lebih mudah memfilter langsung: `df.isna().sum()[df.isna().sum() > 0]`.

**Duplicate records:** 4 baris duplikat penuh (8 baris terlibat pola duplikasi, 4 di antaranya salinan identik).

**Tipe data yang belum sesuai:**

| Kolom | Kondisi | Seharusnya |
|---|---|---|
| `transaction_date` | string dengan **format campur**: `2025-01-01`, `02/01/2025`, `01-03-2025`, `04-Jan-2025`, dst. | datetime |
| `num-of-doors` | teks (`two`, `four`) | numerik (ordinal) |
| `num-of-cylinders` | teks (`two` … `twelve`) | numerik (ordinal) |

**Penulisan kategori tidak konsisten** (huruf besar-kecil & spasi berlebih):

| Kolom | Contoh nilai |
|---|---|
| `make` | `ALFA-ROMERO` vs `alfa-romero`, `Audi` vs `audi`, `dodge␣␣` (spasi di belakang) |
| `body-style` | `SEDAN` vs `Sedan` vs `sedan` |
| `drive-wheels` | `AWD` vs `4wd`, `RWD` vs `rwd` |
| `fuel-system` | `MPFI` vs `Mpfi` vs `mpfi` |

**Permasalahan lain:** beberapa kolom numerik memiliki rentang nilai yang sangat bervariasi (mis. `price` 5.118–45.400 vs `stroke` 2,07–4,17) sehingga belum punya skala seragam; `diesel`/`gas` sudah berupa binary 0/1 (indikasi one-hot dari proses sebelumnya).

---

## 🧹 Data Cleaning

Ringkasan masalah → metode → alasan:

| Masalah | Kolom | Metode | Alasan |
|---|---|---|---|
| NaN | `transaction_date` | **Hapus baris** (2 baris) | Tidak ditemukan pola/korelasi kolom lain yang bisa dipakai mengisi tanggal; mengisi nilai acak justru merusak data |
| NaN kategorikal | `make` | Isi `"unknown"` | Kategorikal nominal tanpa korelasi yang bisa dimanfaatkan; membuang baris sayang karena kolom lain masih berguna |
| NaN kategorikal | `num-of-doors` | Isi `"unknown"`, nanti dipetakan ke `-1` | Kolom ini mempresentasikan angka (ordinal). Daripada menebak-nebak, `unknown` diberi kode `-1` agar tetap terbaca sebagai kategori tersendiri saat pemetaan |
| NaN kategorikal | `horsepower-binned` | Isi via `pd.cut` dari nilai `horsepower` | Kolom ini punya korelasi kuat dengan `horsepower` (Low ≤101, Medium 101–155, High >155), jadi bisa diisi ulang secara deterministik dari kolom pembandingnya |
| NaN numerik | `stroke` | Isi **mean** | Distribusinya relatif simetris (skew ≈ -0,7), mean wakil yang baik |
| NaN numerik | `horsepower` | Isi **median per grup `horsepower-binned`** | Distribusi skewed positif (~1,1) — mean (103,4) jauh dari median (95) & std (37,4). Median per grup binned lebih akurat daripada median global karena menghormati kelompok tenaganya |
| NaN numerik | `price` | Isi **median** | Distribusi skewed positif (~1,83) dengan outlier mobil mahal — median lebih tahan outlier |
| Duplikat | semua kolom | `drop_duplicates()` | Baris salinan identik tidak menambah informasi |
| Format tanggal campur | `transaction_date` | `pd.to_datetime(..., format="mixed")` | Menyeragamkan beberapa format sekaligus menjadi tipe datetime |
| Kategori tak konsisten | `make`, `body-style`, `drive-wheels`, `fuel-system` | `lowercase()` + `strip()` | Menyatukan penulisan agar `SEDAN`/`Sedan`/`sedan` dihitung satu kategori yang sama, dan spasi tersembunyi tidak menciptakan kategori palsu |

**Hasil cleaning:**

| Metrik | Sebelum | Sesudah |
|---|---|---|
| Jumlah baris | 205 | **199** (6 dibuang: 2 NaN `transaction_date` + 4 duplikat) |
| Total sel kosong | 17 | **0** |

---

## 🔄 Data Transformation

| Kolom | Metode | Alasan |
|---|---|---|
| `num-of-doors`, `num-of-cylinders` | **Mapping** teks → angka (`two` → 2, `four` → 4, dst.; `unknown` → -1) | Kolom ini ordinal (memiliki makna urutan/kuantitas). One-hot akan menghilangkan makna tersebut; mapping mempertahankannya dalam bentuk numerik |
| 16 kolom numerik: `normalized-losses`, `wheel-base`, `length`, `width`, `height`, `curb-weight`, `engine-size`, `bore`, `stroke`, `compression-ratio`, `horsepower`, `peak-rpm`, `city-mpg`, `highway-mpg`, `price`, `city-L/100km` | **Min-Max Scaling** ke rentang [0, 1] (`MinMaxScaler`) | Skala antar kolom sangat bervariasi (harga sampai puluhan ribu vs stroke berkoma). Min-Max menyamaratakan rentang tanpa mengubah bentuk distribusi |
| `make`, `aspiration`, `body-style`, `drive-wheels`, `engine-location`, `engine-type`, `fuel-system`, `horsepower-binned` | **One-hot encoding** (`pd.get_dummies`) | Model ML tidak memahami string. 8 kolom kategorikal ini nominal (tanpa urutan), jadi one-hot lebih tepat daripada label encoding |

**Yang sengaja TIDAK dinormalisasi:**

- `num-of-doors` & `num-of-cylinders` → sudah bermakna sebagai angka hasil mapping, dinormalisasi justru menghapus maknanya.
- `symboling` → range-nya sudah serupa skala kecil.
- `diesel` & `gas` → binary 0/1, sudah berada di rentang tepat.

> Catatan dari riset: tidak semua kolom wajib dinormalisasi — kolom label prediksi umumnya dikecualikan. Karena use case pemodelan dataset ini belum ditentukan (label belum diketahui), normalisasi diterapkan ke semua kolom numerik kontinu yang relevan.

### Contoh Sebelum → Sesudah Transformasi

Diambil dari baris pertama dataset:

| Kolom | Sebelum (raw) | Sesudah (processed) | Jenis transformasi |
|---|---|---|---|
| `make` | `alfa-romero` | `make_alfa-romero` = 1 (kolom make lain = 0) | One-hot encoding |
| `body-style` | `convertible` | `body-style_convertible` = 1 (kolom lain = 0) | One-hot encoding |
| `num-of-doors` | `two` | `2` | Mapping ordinal |
| `num-of-cylinders` | `four` | `4` | Mapping ordinal |
| `horsepower` | `111.0` | `0.2944` | Min-Max Scaling |
| `price` | `13495.0` | `0.2080` | Min-Max Scaling |
| `city-mpg` | `21` | `0.2222` | Min-Max Scaling |
| `stroke` | `2.68` | `0.2905` | Min-Max Scaling |
| `transaction_date` | `2025-01-01` (string campur format) | `2025-01-01` (datetime ISO) | Konversi tipe |

**Kolom baru yang dihasilkan:** 53 kolom biner hasil one-hot encoding (mis. `make_alfa-romero`, `body-style_sedan`, `fuel-system_mpfi`, ...) — dataset bertambah dari 30 menjadi **75 kolom**.

---

## 📈 Jumlah Data Sebelum & Sesudah

| Tahap | Baris | Kolom |
|---|---|---|
| Raw (`automobileEDA_dirty_training.csv`) | 205 | 30 |
| Setelah cleaning | 199 | 30 |
| **Processed (`automobileEDA_processed.csv`)** | **199** | **75** |

- Missing values: 17 → **0**
- Baris duplikat dihapus: **4**
- Dataset mentah **tidak pernah ditimpa** — pipeline hanya membacanya.

---

## 🚀 Cara Menjalankan

### 1. Instal dependency

```bash
git clone https://github.com/NafisHandoko/assignment-data-pipeline-nafis-handoko.git
cd assignment-data-pipeline-nafis-handoko

# (opsional tapi disarankan) buat virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

Dependencies (`requirements.txt`): `pandas`, `scikit-learn`, `ipykernel` (ipykernel untuk menjalankan notebook eksplorasi).

### 2. Jalankan pipeline

```bash
python src/pipeline.py
```

Script menggunakan `pathlib.Path` untuk resolve absolute path, jadi aman dijalankan dari direktori mana pun. Ringkasan output di terminal (dipotong untuk keringkasan):

```
Mulai jalankan pipeline...
[load]  .../data/raw/automobileEDA_dirty_training.csv -> 205 baris

===== INSPEKSI DATASET =====
Ukuran dataset: 205 baris x 30 kolom

--- Lima baris pertama ---
...
--- Tipe data setiap kolom ---
...
--- Missing values per kolom ---
transaction_date     2
make                 2
num-of-doors         2
stroke               4
horsepower           3
price                3
horsepower-binned    1

--- Duplicate records: 4 baris ---

--- Nilai unik kolom kategorikal ---
body-style: ['SEDAN', 'Sedan', 'convertible', 'hardtop', 'hatchback', 'sedan', 'wagon']
drive-wheels: ['4wd', 'AWD', 'RWD', 'fwd', 'rwd']
...

[clean] missing values: 17 -> 0
[clean] baris duplikat dihapus: 4
[clean] 205 -> 199 baris (6 dibuang)
[clean] kolom yang berubah: transaction_date, make, num-of-doors, horsepower-binned, stroke, price, horsepower, body-style, drive-wheels, fuel-system
[transform] mapping ordinal + min-max scaling + one-hot encoding
[transform] dataset kini 199 baris x 75 kolom
Pipeline selesai...
```

---

## 🔁 Alur ETL

```
Raw CSV ──► Load Data ──► Data Inspection ──► Data Cleaning ──► Data Transformation ──► Processed CSV
```

| Tahap | Implementasi (`src/pipeline.py`) | Yang dilakukan |
|---|---|---|
| **Extract / Load** | `load_data()` | Baca CSV mentah dari `data/raw/` |
| **Inspection** | `inspect_data()` | Cek shape, tipe data, missing values, duplikat, nilai unik kategorikal — ditampilkan ke terminal saat pipeline dijalankan |
| **Transform (clean)** | `clean_data()` | Tangani missing values, hapus duplikat, seragamkan kategori, perbaiki tipe data |
| **Transform (enrich)** | `transform_data()` | Mapping ordinal, Min-Max Scaling, one-hot encoding |
| **Load / Save** | `save_data()` → `main()` | Simpan hasil ke `data/processed/automobileEDA_processed.csv` |

Seluruh tahap dijalankan berurutan dalam **satu kali eksekusi** `main()` — pipeline dapat dijalankan ulang kapan pun dan selalu menghasilkan output yang sama.

---

## 📂 Lokasi Processed Dataset

```
data/processed/automobileEDA_processed.csv
```

File ini **dibuat otomatis** oleh `pipeline.py` setiap kali dijalankan (bukan salinan manual dari clean dataset referensi).

---

## ✅ Verifikasi

- Pipeline dijalankan end-to-end **tanpa error** (exit code 0).
- Checksum `data/raw/automobileEDA_dirty_training.csv` **identik** sebelum & sesudah eksekusi → dataset mentah tidak berubah.
- Processed dataset bebas missing values (0 NaN) dan terdiri dari 199 baris × 75 kolom.
