# auth.py
import os
import bcrypt
from datetime import datetime
from db import users_col

def _get_secret(key: str, default=None):
    # Prioritas: Streamlit secrets → ENV → default
    try:
        import streamlit as st
        if "secrets" in dir(st) and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)

def create_admin_if_not_exists():
    """
    Seed admin HANYA jika ADMIN_EMAIL & ADMIN_PASSWORD tersedia di secrets/env.
    Tidak ada nilai default di kode agar tidak terekspos di GitHub.
    """
    email = _get_secret("ADMIN_EMAIL")
    password = _get_secret("ADMIN_PASSWORD")
    name = _get_secret("ADMIN_NAME", "Admin")

    # Jika tidak diset, jangan buat apa-apa (aman untuk repo publik)
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
