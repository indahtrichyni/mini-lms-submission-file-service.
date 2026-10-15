from flask import Flask, request, jsonify, send_file
from pathlib import Path
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
import json
import uuid
import mimetypes

app = Flask(__name__)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "submissions"
STORAGE_DIR = ROOT / "storage"
ASSIGNMENTS_FILE = ROOT / "data" / "assignments.json"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".zip", ".png", ".jpg", ".jpeg"}

DATA_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def read_json(path, default=None):
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
    temp_path.replace(path)

def get_submission(submission_id):
    return read_json(DATA_DIR / f"{submission_id}.json")

def public_submission(record):
    # Deliberately omit the internal storage path from all API responses.
    return {
        "submission_id": record["submission_id"],
        "assignment_id": record["assignment_id"],
        "student_id": record["student_id"],
        "file_id": record["file_id"],
        "filename": record["filename"],
        "file_size": record["file_size"],
        "content_type": record["content_type"],
        "status": record["status"],
        "created_at": record["created_at"],
        "download_url": f'/api/files/{record["file_id"]}'
    }

@app.get("/")
def index():
    return jsonify({
        "service": "Mini-LMS Submission/File Service",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/submissions",
            "GET /api/submissions/<submission_id>",
            "GET /api/files/<file_id>"
        ]
    })

@app.post("/api/submissions")
def create_submission():
    # Support both JSON metadata-only requests and multipart file uploads.
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        required = ["assignment_id", "student_id", "filename", "file_size", "content_type"]
        missing = [key for key in required if payload.get(key) in (None, "")]
        if missing:
            return jsonify({
                "error": {
                    "code": "INCOMPLETE_INPUT",
                    "message": "Input wajib belum lengkap.",
                    "fields": missing
                }
            }), 400

        try:
            assignment_id = int(payload["assignment_id"])
            student_id = int(payload["student_id"])
            file_size = int(payload["file_size"])
        except (ValueError, TypeError):
            return jsonify({"error": {"code": "INVALID_INPUT", "message": "assignment_id, student_id, dan file_size harus berupa angka."}}), 400

        filename = secure_filename(str(payload["filename"]))
        content_type = str(payload["content_type"]).strip()
        if not filename:
            return jsonify({"error": {"code": "INVALID_FILENAME", "message": "Nama file tidak valid."}}), 400
        if file_size < 0:
            return jsonify({"error": {"code": "INVALID_FILE_SIZE", "message": "file_size tidak boleh negatif."}}), 400
        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": {"code": "FILE_TOO_LARGE", "message": "Ukuran file melebihi batas 5 MB."}}), 413
        if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
            return jsonify({"error": {"code": "UNSUPPORTED_FILE_TYPE", "message": "Ekstensi file tidak diizinkan."}}), 415
        if not content_type:
            return jsonify({"error": {"code": "INCOMPLETE_INPUT", "message": "content_type wajib diisi."}}), 400

        file_bytes = None
    else:
        payload = request.form
        upload = request.files.get("file")
        required = ["assignment_id", "student_id"]
        missing = [key for key in required if not payload.get(key)]
        if not upload or not upload.filename:
            missing.append("file")
        if missing:
            return jsonify({"error": {"code": "INCOMPLETE_INPUT", "message": "Input wajib belum lengkap.", "fields": missing}}), 400
        try:
            assignment_id = int(payload["assignment_id"])
            student_id = int(payload["student_id"])
        except (ValueError, TypeError):
            return jsonify({"error": {"code": "INVALID_INPUT", "message": "assignment_id dan student_id harus berupa angka."}}), 400
        filename = secure_filename(upload.filename)
        if not filename:
            return jsonify({"error": {"code": "INVALID_FILENAME", "message": "Nama file tidak valid."}}), 400
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            return jsonify({"error": {"code": "UNSUPPORTED_FILE_TYPE", "message": "Ekstensi file tidak diizinkan."}}), 415
        file_bytes = upload.read(MAX_FILE_SIZE + 1)
        file_size = len(file_bytes)
        content_type = upload.mimetype or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": {"code": "FILE_TOO_LARGE", "message": "Ukuran file melebihi batas 5 MB."}}), 413

    assignments = read_json(ASSIGNMENTS_FILE, [])
    if assignment_id not in assignments:
        return jsonify({
            "error": {
                "code": "ASSIGNMENT_NOT_FOUND",
                "message": f"Assignment dengan ID {assignment_id} tidak ditemukan."
            }
        }), 404

    submission_id = str(uuid.uuid4())
    file_id = "f-" + uuid.uuid4().hex[:12]
    storage_name = file_id + Path(filename).suffix.lower()
    storage_path = STORAGE_DIR / storage_name

    if file_bytes is not None:
        storage_path.write_bytes(file_bytes)
    else:
        # Metadata-only mode is supported for the lecture's initial contract example.
        # It does not create a downloadable physical file.
        storage_name = None

    record = {
        "submission_id": submission_id,
        "assignment_id": assignment_id,
        "student_id": student_id,
        "file_id": file_id,
        "filename": filename,
        "file_size": file_size,
        "content_type": content_type,
        "status": "submitted",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "storage_name": storage_name,
        "storage_mode": "uploaded_file" if file_bytes is not None else "metadata_only"
    }
    write_json(DATA_DIR / f"{submission_id}.json", record)
    return jsonify({"data": public_submission(record)}), 201

@app.get("/api/submissions/<submission_id>")
def read_submission(submission_id):
    record = get_submission(submission_id)
    if not record:
        return jsonify({"error": {"code": "SUBMISSION_NOT_FOUND", "message": "Submission tidak ditemukan."}}), 404
    return jsonify({"data": public_submission(record)}), 200

@app.get("/api/files/<file_id>")
def download_file(file_id):
    # Resolve file_id from stored metadata; never accept an internal path from client.
    for metadata_path in DATA_DIR.glob("*.json"):
        record = read_json(metadata_path)
        if record and record.get("file_id") == file_id:
            storage_name = record.get("storage_name")
            if not storage_name:
                return jsonify({"error": {"code": "FILE_CONTENT_NOT_STORED", "message": "Submission ini hanya menyimpan metadata; konten file belum diunggah."}}), 404
            storage_path = (STORAGE_DIR / storage_name).resolve()
            if storage_path.parent != STORAGE_DIR.resolve() or not storage_path.is_file():
                return jsonify({"error": {"code": "FILE_NOT_FOUND", "message": "Konten file tidak ditemukan di storage."}}), 404
            return send_file(storage_path, as_attachment=True, download_name=record["filename"], mimetype=record["content_type"])
    return jsonify({"error": {"code": "FILE_NOT_FOUND", "message": "File ID tidak ditemukan."}}), 404

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
