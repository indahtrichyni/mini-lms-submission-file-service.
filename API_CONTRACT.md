# Kontrak API – Mini-LMS Submission/File Service

Base URL lokal: `http://127.0.0.1:5000`

## 1. POST /api/submissions

Membuat submission baru. Assignment harus ada dalam `data/assignments.json`.

### Pilihan A — unggah file fisik (direkomendasikan untuk demonstrasi)
`Content-Type: multipart/form-data`

| Field | Tipe | Wajib | Keterangan |
|---|---|---:|---|
| `assignment_id` | integer | Ya | ID assignment yang tersedia |
| `student_id` | integer | Ya | ID mahasiswa |
| `file` | file | Ya | File `.txt`, `.pdf`, `.zip`, `.png`, `.jpg`, atau `.jpeg`, maksimum 5 MB |

### Pilihan B — metadata saja
`Content-Type: application/json`

```json
{
  "assignment_id": 501,
  "student_id": 101,
  "filename": "uts-mini-lms.zip",
  "file_size": 248000,
  "content_type": "application/zip"
}
```
Field wajib: `assignment_id`, `student_id`, `filename`, `file_size`, `content_type`. Mode ini tidak mengunggah isi file.

### Respons berhasil — 201 Created
```json
{
  "data": {
    "submission_id": "UUID",
    "assignment_id": 501,
    "student_id": 101,
    "file_id": "f-xxxxxxxxxxxx",
    "filename": "jawaban.txt",
    "file_size": 18,
    "content_type": "text/plain",
    "status": "submitted",
    "created_at": "waktu ISO-8601",
    "download_url": "/api/files/f-xxxxxxxxxxxx"
  }
}
```

### Respons gagal
- `400 Bad Request`: field wajib hilang atau format input tidak valid.
- `404 Not Found`: assignment tidak ditemukan.
- `413 Payload Too Large`: file melebihi 5 MB.
- `415 Unsupported Media Type`: ekstensi file tidak diizinkan.

Contoh error:
```json
{
  "error": {
    "code": "INCOMPLETE_INPUT",
    "message": "Input wajib belum lengkap.",
    "fields": ["student_id", "file"]
  }
}
```

## 2. GET /api/submissions/{submission_id}

Mengambil metadata submission yang sudah tersimpan.

### Berhasil — 200 OK
Mengembalikan objek `data` dengan struktur metadata yang sama seperti respons POST. Path internal tidak disertakan.

### Gagal — 404 Not Found
```json
{
  "error": {
    "code": "SUBMISSION_NOT_FOUND",
    "message": "Submission tidak ditemukan."
  }
}
```

## 3. GET /api/files/{file_id}

Mengunduh isi file menggunakan `file_id`, bukan lokasi internal.

- `200 OK`: konten file dikirim sebagai attachment.
- `404 Not Found`: file ID tidak dikenal, isi file tidak ada, atau submission dibuat dengan mode metadata saja.

## Identifier dan penyimpanan
- `submission_id` mengidentifikasi catatan submission.
- `file_id` adalah identifier publik yang dipakai client untuk mengakses file.
- Metadata JSON disimpan di `data/submissions/`.
- Isi file disimpan terpisah di `storage/` dengan nama internal unik yang dibuat service.
- Respons publik tidak memuat path lokal.
