# Mini-LMS Submission/File Service

Proyek kelompok untuk mata kuliah **Sistem Terdistribusi — Pertemuan 6**. Aplikasi ini merupakan prototipe layanan API untuk menerima submission tugas, menyimpan metadata dalam JSON, dan menyediakan akses file melalui identifier.

> Teknologi: Python, Flask, JSON, REST API, Postman.

## Fitur

- `POST /api/submissions` — membuat submission melalui JSON metadata atau unggahan `multipart/form-data`.
- `GET /api/submissions/<submission_id>` — mengambil metadata submission.
- `GET /api/files/<file_id>` — mengunduh file yang benar-benar diunggah.
- Validasi assignment, input wajib, tipe file, dan ukuran maksimum file.
- Metadata dan konten file disimpan terpisah.
- Path penyimpanan internal tidak ditampilkan dalam respons API.

## Struktur Proyek

```text
mini_lms_file_service/
├── app.py
├── requirements.txt
├── README.md
├── API_CONTRACT.md
├── data/
│   ├── assignments.json
│   └── submissions/       # Metadata submission JSON dibuat saat runtime
├── storage/               # File fisik yang diunggah
├── tests/
│   └── test_app.py
└── evidence/              # Screenshot hasil pengujian kelompok
```

## Persyaratan

- Python 3.10 atau lebih baru
- pip
- Postman (opsional, untuk pengujian melalui antarmuka)

## Cara Menjalankan di Windows

Buka CMD pada folder proyek, lalu jalankan:

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py app.py
```

Server berjalan di `http://127.0.0.1:5000`. Biarkan terminal server tetap terbuka saat melakukan pengujian.

## Pengujian API

### 1. Memeriksa layanan

Method: `GET`

URL: `http://127.0.0.1:5000/`

Respons yang diharapkan: `200 OK` dan daftar endpoint.

### 2. Submission valid dengan unggahan file

Buat file teks bernama `jawaban.txt`, kemudian jalankan dari terminal CMD kedua:

```bat
curl.exe -X POST http://127.0.0.1:5000/api/submissions -F "assignment_id=501" -F "student_id=101" -F "file=@jawaban.txt;type=text/plain"
```

Respons yang diharapkan: `201 Created`. Catat `submission_id` dan `file_id` pada respons.

### 3. Mengambil detail submission

Ganti `<submission_id>` dengan ID dari respons POST:

```bat
curl.exe http://127.0.0.1:5000/api/submissions/<submission_id>
```

Respons yang diharapkan: `200 OK` jika submission ditemukan.

### 4. Mengunduh file

Ganti `<file_id>` dengan ID dari respons POST:

```bat
curl.exe -OJ http://127.0.0.1:5000/api/files/<file_id>
```

Untuk uji unduhan, gunakan submission yang dibuat melalui unggahan file fisik, bukan mode JSON metadata saja.

### 5. Assignment tidak ditemukan

Gunakan ID yang tidak tercantum pada `data/assignments.json`:

```bat
curl.exe -i -X POST http://127.0.0.1:5000/api/submissions -F "assignment_id=999999" -F "student_id=101" -F "file=@jawaban.txt;type=text/plain"
```

Hasil yang diharapkan: `404 Not Found`.

### 6. Input tidak lengkap

```bat
curl.exe -i -X POST http://127.0.0.1:5000/api/submissions -F "assignment_id=501"
```

Hasil yang diharapkan: `400 Bad Request` dengan kode kesalahan `INCOMPLETE_INPUT`.

### Mode JSON metadata saja

API juga menerima JSON yang berisi metadata file tanpa konten file fisik. Mode ini berguna untuk menguji pencatatan metadata, tetapi tidak membuktikan upload atau download file fisik.

```json
{
  "assignment_id": 501,
  "student_id": 101,
  "filename": "jawaban.txt",
  "file_size": 100,
  "content_type": "text/plain"
}
```

Kirim ke `POST /api/submissions` dengan header `Content-Type: application/json`.

## Kontrak API

Detail field wajib, contoh request/response, identifier, serta status HTTP dijelaskan pada [`API_CONTRACT.md`](API_CONTRACT.md).

## Model Data dan Penyimpanan

- `submission_id`: UUID untuk mengidentifikasi satu submission.
- `file_id`: identifier publik untuk mengakses file melalui endpoint GET.
- Metadata: disimpan sebagai file JSON pada `data/submissions/`.
- Konten file: disimpan terpisah pada direktori `storage/` menggunakan nama internal yang dibuat oleh aplikasi.
- Path penyimpanan internal tidak dikembalikan kepada client.
- Daftar assignment demo berada di `data/assignments.json` dan bukan integrasi dengan layanan assignment eksternal.

## Bukti Pengujian

Simpan screenshot asli Postman atau CMD ke folder `evidence/` dengan nama berikut:

1. `01-valid-submission.png` — POST valid, `201 Created`.
2. `02-assignment-not-found.png` — assignment tidak ditemukan, `404 Not Found`.
3. `03-incomplete-input.png` — input tidak lengkap, `400 Bad Request`.

Screenshot harus diambil dari pengujian yang benar-benar dijalankan oleh kelompok. Jangan mengisi folder dengan screenshot contoh yang tidak berasal dari pengujian aktual.

## Kontribusi Anggota Kelompok

| No. | Nama | NIM | Kontribusi |
|---:|---|---|---|
| 1 | Indah Tricahyani | 240209501078 | Koordinasi integrasi proyek, penyusunan README, dan pemeriksaan kelengkapan hasil. |
| 2 | Aulia Aqilah | 230209552025 | Membantu implementasi serta pemeriksaan endpoint submission dan validasi input. |
| 3 | Mutia Inayah | 240209501038 | Membantu pengujian API, pencatatan hasil, dan penyiapan bukti screenshot. |
| 4 | Arjun | 240209502022 | Membantu penyusunan kontrak API serta pemeriksaan model metadata dan penyimpanan file. |

**Catatan:** Pembagian di atas merupakan draf. Pastikan peran setiap anggota sesuai dengan kontribusi yang benar-benar dilakukan sebelum dikumpulkan.

## Batasan Prototipe

Aplikasi menggunakan data assignment contoh dan penyimpanan lokal. Autentikasi, otorisasi berdasarkan identitas mahasiswa, integrasi database produksi, antivirus, dan object storage belum termasuk dalam prototipe ini.
