# Data Pipeline: Automobile Dataset

Pipeline sederhana dengan Python + Pandas untuk mengolah dataset otomotif dari bentuk mentah sampai siap dipakai untuk analisis atau pemodelan: **Load → Inspection → Cleaning → Transformation → Save**.

Tugas individual untuk materi **Data Engineering: Pipeline & Preparation** (Rework Academy, Sesi 3).

---

## Deskripsi Dataset

Dataset berisi data spesifikasi mobil (engine-size, horsepower, curb-weight, body-style, dst.) plus atribut transaksi (`transaction_date`, `price`). Ukurannya **205 baris × 30 kolom**.

Dataset disediakan mentor lewat [s.id/dataset-sesi-3](https://s.id/dataset-sesi-3) (`Dataset_Sesi_3.zip`), isinya tiga file:

| File | Dipakai untuk |
|---|---|
| `automobileEDA_dirty_training.csv` | dataset utama, input pipeline |
| `automobileEDA.csv` | dataset original, hanya sebagai referensi |
| `automobile_processed.csv` | clean dataset, hanya untuk membandingkan hasil |

Hasil akhir seluruhnya dibuat oleh `src/pipeline.py`, bukan disalin dari clean dataset referensi.

---

## Struktur Folder

```
assignment-data-pipeline-nafis-handoko/
├── data/
│   ├── raw/
│   │   ├── automobileEDA_dirty_training.csv   # dataset mentah (tidak pernah ditimpa)
│   │   ├── cleaned.csv                        # hasil antara tahap cleaning (dari notebook)
│   │   └── normalized.csv                     # hasil antara tahap transformasi (dari notebook)
│   └── processed/
│       └── automobileEDA_processed.csv        # hasil akhir pipeline
├── src/
│   ├── pipeline.py                            # script pipeline, bisa dijalankan ulang
│   └── pipeline.ipynb                         # notebook eksplorasi
├── README.md
└── requirements.txt
```

---

## Kondisi Awal Dataset

**Catatan kecil:** `df.shape` menunjukkan `(205, 30)`, padahal waktu kucek langsung di file ada 206 baris. Ternyata baris pertama dipakai Pandas sebagai nama kolom, jadi tidak ikut terhitung.

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

> Dengan 30 kolom, hasil `df.isna().sum()` gampang ada yang kelewat mata. Biar cepat, langsung filter saja: `df.isna().sum()[df.isna().sum() > 0]`.

**Duplicate records:** 4 baris. Keempatnya ada di ujung dataset (baris 201–204), dan masing-masing salinan persis dari baris 5, 25, 60, dan 100.

**Tipe data yang belum pas:**

| Kolom | Kondisi | Seharusnya |
|---|---|---|
| `transaction_date` | string dengan format campur: `2025-01-01`, `02/01/2025`, `01-03-2025`, `04-Jan-2025`, dst. | datetime |
| `num-of-doors` | teks (`two`, `four`) | angka |
| `num-of-cylinders` | teks (`two` … `twelve`) | angka |

**Penulisan kategori tidak konsisten** — campuran huruf besar-kecil dan spasi berlebih:

| Kolom | Contoh nilainya |
|---|---|
| `make` | `ALFA-ROMERO` vs `alfa-romero`, `Audi` vs `audi`, `dodge␣␣` (ada spasi di belakang) |
| `body-style` | `SEDAN` vs `Sedan` vs `sedan` |
| `drive-wheels` | `AWD` vs `4wd`, `RWD` vs `rwd` |
| `fuel-system` | `MPFI` vs `Mpfi` vs `mpfi` |

**Masalah lain:** rentang nilai antar kolom numerik beda-beda jauh — `price` dari 5.118 sampai 45.400, `stroke` cuma 2,07 sampai 4,17 — jadi belum ada skala yang seragam. Sementara `diesel` dan `gas` sudah berisi 0/1, kemungkinan sisa one-hot encoding dari proses sebelumnya.

---

## Data Cleaning

Ringkasan masalah, cara menanganinya, dan alasannya:

| Masalah | Kolom | Metode | Alasan |
|---|---|---|---|
| NaN | `transaction_date` | Hapus 2 barisnya | Tidak ada kolom lain yang bisa dijadikan patokan untuk mengisi tanggal, jadi mengisi dengan tebakan malah bikin data bohong. Diputuskan dihapus saja. |
| NaN kategorikal | `make` | Isi `"unknown"` | Tidak ada pembanding yang bisa dipakai, tapi barisnya sayang dibuang karena kolom lain masih lengkap. |
| NaN kategorikal | `num-of-doors` | Isi `"unknown"`, nanti dipetakan ke `-1` | Isi kolom ini sebenarnya angka (`two`, `four`). Kalau ditebak-tebakan, tebakannya ikut kebawa ke analisis. Jadi `unknown` dikode `-1` supaya tetap terbaca sebagai kelompok tersendiri saat pemetaan. |
| NaN kategorikal | `horsepower-binned` | Hitung ulang dari kolom `horsepower` (`pd.cut`) | Kolom ini berhubungan langsung dengan `horsepower`, jadi nilai kosongnya bisa dihitung ulang: Low sampai 101, Medium 101–155, High di atasnya. |
| NaN numerik | `stroke` | Isi mean | Sebarannya lumayan merata (skew ≈ -0,7), jadi mean cukup mewakili. |
| NaN numerik | `horsepower` | Isi median per kelompok `horsepower-binned` | Sebarannya miring (skew ≈ 1,1): mean 103,4 tapi median cuma 95. Median per kelompok lebih masuk akal daripada median seisi kolom, karena mobil kelompok Low dan High jelas beda tenaganya. |
| NaN numerik | `price` | Isi median | Skew 1,83, dan ada beberapa mobil yang harganya jauh di atas yang lain. Median tidak tergeser oleh nilai ekstrem seperti mean. |
| Duplikat | semua kolom | `drop_duplicates()` | Baris kembar tidak menambah informasi apa-apa. |
| Format tanggal campur | `transaction_date` | `pd.to_datetime(..., format="mixed")` | Satu parameter ini bisa menyeragamkan semua format sekaligus ke tipe datetime. |
| Kategori tidak konsisten | `make`, `body-style`, `drive-wheels`, `fuel-system` | lowercase + strip | Supaya `SEDAN`, `Sedan`, dan `sedan` dihitung satu kategori yang sama, dan spasi di belakang (`dodge␣␣`) tidak menciptakan kategori palsu. |

**Hasil cleaning:**

| Metrik | Sebelum | Sesudah |
|---|---|---|
| Jumlah baris | 205 | **199** (6 dibuang: 2 NaN `transaction_date` + 4 duplikat) |
| Total sel kosong | 17 | **0** |

---

## Data Transformation

| Kolom | Metode | Alasan |
|---|---|---|
| `num-of-doors`, `num-of-cylinders` | Mapping teks → angka (`two` → 2, `four` → 4, dst.; `unknown` → -1) | Isi aslinya angka yang ditulis sebagai teks. Mapping mengembalikan maknanya; kalau one-hot, makna urutannya justru hilang. |
| 16 kolom numerik: `normalized-losses`, `wheel-base`, `length`, `width`, `height`, `curb-weight`, `engine-size`, `bore`, `stroke`, `compression-ratio`, `horsepower`, `peak-rpm`, `city-mpg`, `highway-mpg`, `price`, `city-L/100km` | Min-Max Scaling ke rentang 0–1 (`MinMaxScaler`) | Skala antar kolom beda jauh — harga sampai puluhan ribu, stroke cuma berkoma. Min-Max menyamakan rentang tanpa mengubah bentuk sebarannya. |
| `make`, `aspiration`, `body-style`, `drive-wheels`, `engine-location`, `engine-type`, `fuel-system`, `horsepower-binned` | One-hot encoding (`pd.get_dummies`) | Model machine learning tidak bisa membaca string, dan kategori di kolom-kolom ini tidak berurutan, jadi one-hot lebih pas daripada label encoding. |

Yang sengaja **tidak** dinormalisasi:

- `num-of-doors` & `num-of-cylinders` — sudah jadi angka hasil mapping; dinormalisasi malah menghapus maknanya.
- `symboling` — rentangnya cuma -2 sampai 3.
- `diesel` & `gas` — sudah 0/1, sesuai rentang yang dituju.

> Dari riset singkat: tidak semua kolom harus dinormalisasi. Kolom yang jadi label prediksi biasanya dikeluarkan. Karena di dataset ini labelnya belum ditentukan (belum jelas mau dipakai untuk prediksi apa), semua kolom numerik kontinu sekalian dinormalisasi.

### Contoh Sebelum → Sesudah Transformasi

Semua diambil dari baris pertama dataset:

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
| `transaction_date` | `2025-01-01` (string, format campur) | `2025-01-01` (datetime ISO) | Konversi tipe |

**Kolom baru:** 53 kolom 0/1 hasil one-hot encoding (`make_alfa-romero`, `body-style_sedan`, `fuel-system_mpfi`, dst.) — dataset bertambah dari 30 menjadi **75 kolom**.

---

## Jumlah Data Sebelum & Sesudah

| Tahap | Baris | Kolom |
|---|---|---|
| Raw (`automobileEDA_dirty_training.csv`) | 205 | 30 |
| Setelah cleaning | 199 | 30 |
| **Processed (`automobileEDA_processed.csv`)** | **199** | **75** |

- Missing values: 17 → 0
- Baris duplikat yang dihapus: 4
- Dataset mentah tidak pernah ditimpa — pipeline hanya membacanya.

---

## Cara Menjalankan

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

Dependencies di `requirements.txt`: `pandas`, `scikit-learn`, dan `ipykernel` (yang terakhir untuk menjalankan notebook eksplorasinya).

### 2. Jalankan pipeline

```bash
python src/pipeline.py
```

Script memakai `pathlib.Path` untuk resolve path absolut, jadi bisa dijalankan dari folder mana pun. Ringkasan output di terminal (dipotong biar singkat):

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

## Alur ETL

```
Raw CSV ──► Load Data ──► Data Inspection ──► Data Cleaning ──► Data Transformation ──► Processed CSV
```

| Tahap | Implementasi (`src/pipeline.py`) | Yang dilakukan |
|---|---|---|
| **Extract / Load** | `load_data()` | Baca CSV mentah dari `data/raw/` |
| **Inspection** | `inspect_data()` | Cek ukuran, tipe data, missing values, duplikat, dan nilai unik kategorikal — hasilnya tampil di terminal saat pipeline jalan |
| **Transform (clean)** | `clean_data()` | Tangani missing values, hapus duplikat, seragamkan kategori, perbaiki tipe data |
| **Transform (enrich)** | `transform_data()` | Mapping ordinal, Min-Max Scaling, one-hot encoding |
| **Load / Save** | `save_data()` → `main()` | Simpan hasil ke `data/processed/automobileEDA_processed.csv` |

Semua tahap jalan berurutan dalam satu kali eksekusi `main()`. Pipeline bisa dijalankan ulang kapan saja dan hasilnya konsisten.

---

## Lokasi Processed Dataset

```
data/processed/automobileEDA_processed.csv
```

File ini dibuat otomatis setiap kali `pipeline.py` dijalankan — bukan salinan manual dari clean dataset referensi.

---

## Verifikasi

- Pipeline dijalankan dari awal sampai akhir tanpa error.
- Checksum `data/raw/automobileEDA_dirty_training.csv` sebelum dan sesudah eksekusi identik — dataset mentah tidak berubah.
- Hasil akhir bersih dari missing values: 199 baris × 75 kolom.
