# utils.py
import os
import uuid
import base64
from datetime import datetime

STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

def save_uploaded_file(uploaded_file):
    """
    Simpan file upload ke STORAGE_DIR dengan nama unik.
    Returns full path.
    """
    ext = os.path.splitext(uploaded_file.name)[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(STORAGE_DIR, unique_name)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path

def file_to_base64(file_path):
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def month_label(dt):
    return dt.strftime("%Y-%m")
