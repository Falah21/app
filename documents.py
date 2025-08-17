# documents.py
from db import docs_col, categories_col
from utils import save_uploaded_file
from datetime import datetime
from bson.objectid import ObjectId
import os

def ensure_default_categories():
    defaults = ["Keuangan", "SDM", "Administrasi", "Lainnya"]
    for c in defaults:
        if not categories_col.find_one({"name": c}):
            categories_col.insert_one({"name": c})

def list_categories():
    return [c["name"] for c in categories_col.find()]

def add_category(name):
    if categories_col.find_one({"name": name}):
        return False
    categories_col.insert_one({"name": name})
    return True

def remove_category(name):
    categories_col.delete_one({"name": name})
    return True

def upload_document(title, category, description, year, uploaded_file, uploader_id):
    path = save_uploaded_file(uploaded_file)
    doc = {
        "title": title,
        "category": category,
        "description": description,
        "year": int(year),
        "file_path": path,
        "original_filename": uploaded_file.name,
        "uploader_id": uploader_id,
        "uploaded_at": datetime.utcnow()
    }
    res = docs_col.insert_one(doc)
    return str(res.inserted_id)

def list_documents(filters=None):
    q = filters or {}
    # if querying by uploader_id string, caller should convert
    docs = list(docs_col.find(q).sort("uploaded_at", -1))
    return docs

def get_document(doc_id):
    return docs_col.find_one({"_id": ObjectId(doc_id)})

def update_metadata(doc_id, data):
    docs_col.update_one({"_id": ObjectId(doc_id)}, {"$set": data})

def replace_file(doc_id, uploaded_file):
    doc = get_document(doc_id)
    if not doc:
        return False, "Dokumen tidak ditemukan"
    # hapus file lama jika ada
    old_path = doc.get("file_path")
    if old_path and os.path.exists(old_path):
        os.remove(old_path)
    new_path = save_uploaded_file(uploaded_file)
    docs_col.update_one({"_id": ObjectId(doc_id)}, {"$set": {
        "file_path": new_path,
        "original_filename": uploaded_file.name,
        "uploaded_at": datetime.utcnow()
    }})
    return True, "File diganti"

def delete_document(doc_id):
    doc = get_document(doc_id)
    if not doc:
        return False
    # hapus file fisik
    path = doc.get("file_path")
    if path and os.path.exists(path):
        os.remove(path)
    docs_col.delete_one({"_id": ObjectId(doc_id)})
    return True
