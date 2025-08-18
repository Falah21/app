import streamlit as st
import pandas as pd
from auth import register_user, login_user, create_admin_if_not_exists
from documents import (
    ensure_default_categories, list_categories, add_category, remove_category,
    upload_document, list_documents, delete_document
)
from db import users_col
from utils import file_to_base64
from datetime import datetime
import os, base64

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="Aplikasi Arsip KPU Kota Surabaya", layout="wide")
ensure_default_categories()
create_admin_if_not_exists()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "landing"

# ---------------------------
# Helper
# ---------------------------
def preview_pdf_inline(file_path, height=600):
    if not os.path.exists(file_path):
        st.error("File tidak ditemukan di server.")
        return
    b64 = file_to_base64(file_path)
    iframe = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="{height}"></iframe>'
    st.markdown(iframe, unsafe_allow_html=True)

def get_logo_base64():
    if os.path.exists("logo_kpu.png"):
        with open("logo_kpu.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

# ---------------------------
# Navbar
# ---------------------------
def navbar():
    logo_b64 = get_logo_base64()
    col1, col2, col3, col4, col5 = st.columns([1,2,1,1,1])
    with col1:
        if logo_b64:
            st.image(base64.b64decode(logo_b64), width=50)
    with col2:
        if st.button("About"):
            st.session_state.page = "about"
    with col3:
        if st.button("Helpdesk"):
            st.session_state.page = "helpdesk"
    with col4:
        if st.button("Blog"):
            st.session_state.page = "blog"
    with col5:
        if st.button("Login"):
            st.session_state.page = "login"

# ---------------------------
# Pages
# ---------------------------
def page_landing():
    navbar()
    st.markdown("""
    <div style="padding:40px;">
        <h1 style="color:#800000;">Aplikasi Arsip KPU Kota Surabaya</h1>
        <p>Selamat datang di aplikasi digitalisasi arsip KPU. 
        Pengelolaan arsip yang profesional, aman, dan mudah untuk mendukung transparansi dan akuntabilitas publik.</p>
    </div>
    """, unsafe_allow_html=True)

def page_about():
    navbar()
    st.title("Tentang Aplikasi")
    st.write("📌 Aplikasi Arsip KPU Kota Surabaya dibuat untuk mendigitalisasi arsip dokumen agar lebih mudah diakses, aman, dan transparan.")

def page_helpdesk():
    navbar()
    st.title("Helpdesk")
    st.write("☎️ Hubungi helpdesk KPU Surabaya di email: **helpdesk@kpu.go.id** atau telepon: (031) 1234567")

def page_blog():
    navbar()
    st.title("Blog")
    st.write("📰 Artikel & update terbaru seputar arsip KPU akan muncul di sini.")

def page_login():
    navbar()
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not email or not password:
            st.error("Isi semua field.")
        else:
            ok, res = login_user(email.strip(), password)
            if ok:
                st.session_state.logged_in = True
                st.session_state.user = res
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error(res)

    if st.button("Registrasi"):
        st.session_state.page = "register"
        st.rerun()

def page_register():
    navbar()
    st.title("Registrasi")
    r_name = st.text_input("Nama Lengkap")
    r_email = st.text_input("Email")
    r_pass = st.text_input("Password", type="password")
    r_role = st.selectbox("Role", ["staf", "viewer"])

    if st.button("Daftar"):
        if not r_name or not r_email or not r_pass:
            st.error("Harap isi semua field.")
        else:
            ok, msg = register_user(r_name.strip(), r_email.strip(), r_pass, r_role)
            if ok:
                st.success(msg + " Silakan login.")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(msg)

    if st.button("Kembali ke Login"):
        st.session_state.page = "login"
        st.rerun()

# ---------------------------
# Dashboard
# ---------------------------
def page_dashboard():
    user = st.session_state.user
    role = user.get("role", "viewer")
    st.sidebar.write(f"👤 {user['name']} — ({role})")

    menu_items = ["Dashboard", "Upload Dokumen", "Lihat Arsip", "Pencarian & Filter"]
    if role == "admin":
        menu_items.extend(["Kelola Kategori", "Manajemen User"])
    menu_items.append("Logout")

    choice = st.sidebar.radio("Menu", menu_items)

    if choice == "Dashboard":
        st.title("Dashboard")
        docs = list_documents()
        st.metric("Total Dokumen", len(docs))

    elif choice == "Upload Dokumen":
        st.title("Upload Dokumen")
        with st.form("upload_form"):
            title = st.text_input("Judul dokumen")
            category = st.selectbox("Kategori", list_categories())
            description = st.text_area("Deskripsi singkat")
            year = st.number_input("Tahun", min_value=1900, max_value=2100, value=datetime.utcnow().year)
            file = st.file_uploader("Pilih file PDF", type=["pdf"])
            submitted = st.form_submit_button("Upload")
        if submitted and file and title:
            upload_document(title, category, description, year, file, user["_id"])
            st.success("Dokumen berhasil diupload.")

    elif choice == "Lihat Arsip":
        st.title("Daftar Dokumen")
        docs = list_documents()
        if not docs:
            st.info("Belum ada dokumen.")
        else:
            for d in docs:
                st.write(f"**{d.get('title')}** — {d.get('category')} ({d.get('year')})")
                if os.path.exists(d.get("file_path", "")):
                    preview_pdf_inline(d["file_path"], height=400)

    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.page = "landing"
        st.rerun()

# ---------------------------
# ROUTING
# ---------------------------
if not st.session_state.logged_in:
    if st.session_state.page == "landing":
        page_landing()
    elif st.session_state.page == "login":
        page_login()
    elif st.session_state.page == "register":
        page_register()
    elif st.session_state.page == "about":
        page_about()
    elif st.session_state.page == "helpdesk":
        page_helpdesk()
    elif st.session_state.page == "blog":
        page_blog()
    else:
        page_landing()
else:
    page_dashboard()
