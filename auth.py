# auth.py
import os
import bcrypt
from datetime import datetime
from db import users_col

def _get_secret(key: str, default=None):
    try:
        import streamlit as st
        if "secrets" in dir(st) and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

def create_admin_if_not_exists():
    email = _get_secret("ADMIN_EMAIL")
    password = _get_secret("ADMIN_PASSWORD")
    name = _get_secret("ADMIN_NAME", "Admin")

    if not email or not password:
        return False
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
        user.pop("password", None)  # hapus hash dari dict
        return True, user
    return False, "Email atau password salah"
