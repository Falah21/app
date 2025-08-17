# auth.py
import bcrypt
from datetime import datetime
from db import users_col

def create_admin_if_not_exists(email="admin@company.local", password="admin123", name="Admin"):
    """
    Convenience: buat akun admin default (jalankan sekali jika perlu).
    """
    if users_col.find_one({"email": email}):
        return False
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    users_col.insert_one({
        "name": name,
        "email": email,
        "password": hashed,
        "role": "admin",
        "active": True,
        "created_at": datetime.utcnow()
    })
    return True

def register_user(name, email, password, role="staf"):
    if users_col.find_one({"email": email}):
        return False, "Email sudah terdaftar"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    users_col.insert_one({
        "name": name,
        "email": email,
        "password": hashed,
        "role": role,
        "active": True,
        "created_at": datetime.utcnow()
    })
    return True, "Registrasi berhasil"

def login_user(email, password):
    user = users_col.find_one({"email": email, "active": True})
    if not user:
        return False, "Akun tidak ditemukan atau nonaktif"
    if bcrypt.checkpw(password.encode(), user["password"]):
        # remove password bytes before returning
        user.pop("password", None)
        return True, user
    return False, "Email atau password salah"
