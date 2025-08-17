import streamlit as st
import pandas as pd
from auth import register_user, login_user, create_admin_if_not_exists
from documents import (
    ensure_default_categories, list_categories, add_category, remove_category,
    upload_document, list_documents, update_metadata, replace_file, delete_document
)
from db import users_col
from utils import file_to_base64
from datetime import datetime
import os

st.set_page_config(page_title="Aplikasi Arsip KPU Kota Surabaya", layout="wide")

# ---------------------------
# Setup awal
# ---------------------------
ensure_default_categories()
create_admin_if_not_exists()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"

# ---------------------------
# Helper: Preview PDF
# ---------------------------
def preview_pdf_inline(file_path, height=600):
    if not os.path.exists(file_path):
        st.error("File tidak ditemukan di server.")
        return
    b64 = file_to_base64(file_path)
    href = f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="{height}"></iframe>'
    st.markdown(href, unsafe_allow_html=True)

# ---------------------------
# UI: Header
# ---------------------------
def header_kpu():
    # pastikan logo ada di folder project
    if os.path.exists("logo_kpu.png"):
        st.image("logo_kpu.png", width=120)
    st.markdown(
        "<h2 style='text-align:center; color:#B22222;'>Aplikasi Arsip KPU Kota Surabaya</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center; font-size:16px;'>Selamat datang di aplikasi digitalisasi arsip KPU</p>",
        unsafe_allow_html=True
    )

# ---------------------------
# Login Page
# ---------------------------
def page_login():
    header_kpu()
    st.markdown("### Login")
    email = st.text_input("Email", placeholder="Masukkan email anda")
    password = st.text_input("Password", placeholder="Masukkan password anda", type="password")

    st.markdown("<a style='font-size:12px; color:#B22222;' href='#'>Lupa kata sandi?</a>", unsafe_allow_html=True)

    if st.button("Login", use_container_width=True):
        if not email or not password:
            st.error("Harap isi semua field.")
        else:
            ok, res = login_user(email.strip(), password)
            if ok:
                st.session_state.logged_in = True
                st.session_state.user = res
                st.rerun()
            else:
                st.error(res)

    st.markdown("<p style='text-align:center;'>Belum punya akun?</p>", unsafe_allow_html=True)
    if st.button("Registrasi", use_container_width=True):
        st.session_state.auth_page = "register"
        st.rerun()

# ---------------------------
# Register Page
# ---------------------------
def page_register():
    header_kpu()
    st.markdown("### Registrasi")
    r_name = st.text_input("Nama Lengkap", placeholder="Masukkan nama anda")
    r_email = st.text_input("Email", placeholder="Masukkan email anda")
    r_pass = st.text_input("Password", placeholder="Masukkan password anda", type="password")
    r_role = st.selectbox("Role", ["staf", "viewer"])

    if st.button("Registrasi", use_container_width=True):
        if not r_name or not r_email or not r_pass:
            st.error("Harap isi semua field.")
        else:
            ok, msg = register_user(r_name.strip(), r_email.strip(), r_pass, role=r_role)
            if ok:
                st.success(msg + " Silakan login.")
                st.session_state.auth_page = "login"
                st.rerun()
            else:
                st.error(msg)

    if st.button("Kembali ke Login", use_container_width=True):
        st.session_state.auth_page = "login"
        st.rerun()

# ---------------------------
# Dashboard & Menu
# ---------------------------
def page_dashboard():
    user = st.session_state.user
    role = user.get("role", "viewer")
    st.sidebar.write(f"👤 {user['name']} — ({role})")

    menu_items = ["Dashboard", "Upload Dokumen", "Lihat Arsip", "Pencarian & Filter"]
    if role == "admin":
        menu_items.append("Kelola Kategori")
        menu_items.append("Manajemen User")
    menu_items.append("Logout")

    choice = st.sidebar.radio("Menu", menu_items)

    # ----------------- Dashboard -----------------
    if choice == "Dashboard":
        st.title("Dashboard")
        docs = list_documents()
        total = len(docs)
        st.metric("Total Dokumen", total)

        cats = list_categories()
        counts = {c: 0 for c in cats}
        for d in docs:
            counts[d.get("category", "Lainnya")] = counts.get(d.get("category", "Lainnya"), 0) + 1
        st.subheader("Jumlah dokumen per kategori")
        df_cat = pd.DataFrame([{"Kategori": k, "Jumlah": v} for k, v in counts.items()])
        st.dataframe(df_cat)

        per_month = {}
        for d in docs:
            dt = d.get("uploaded_at")
            if dt:
                ym = dt.strftime("%Y-%m")
                per_month[ym] = per_month.get(ym, 0) + 1
        st.subheader("Upload per bulan")
        if per_month:
            df_month = pd.DataFrame(sorted(
                [{"Bulan": k, "Jumlah": v} for k, v in per_month.items()],
                key=lambda x: x["Bulan"]))
            st.dataframe(df_month)
        else:
            st.info("Belum ada aktivitas upload.")

    # ----------------- Upload -----------------
    elif choice == "Upload Dokumen":
        st.title("Upload Dokumen")
        with st.form("upload_form"):
            title = st.text_input("Judul dokumen")
            category = st.selectbox("Kategori", list_categories())
            description = st.text_area("Deskripsi singkat")
            year = st.number_input("Tahun dokumen", min_value=1900, max_value=2100, value=datetime.utcnow().year)
            file = st.file_uploader("Pilih file PDF", type=["pdf"])
            submitted = st.form_submit_button("Upload")
        if submitted:
            if not title or not file:
                st.error("Judul dan file wajib diisi.")
            else:
                doc_id = upload_document(title.strip(), category, description.strip(), year, file, user["_id"])
                st.success("Dokumen berhasil diupload (ID: %s)" % doc_id)

    # ----------------- Lihat Arsip -----------------
    # ----------------- Lihat Arsip -----------------
    elif choice == "Lihat Arsip":
        st.title("Daftar Dokumen")
        docs = list_documents()
        if not docs:
            st.info("Belum ada dokumen.")
        else:
            # ================= Tabel Ringkas =================
            st.subheader("📑 Tabel Daftar Dokumen")
            table_data = []
            for i, d in enumerate(docs, start=1):
                table_data.append({
                    "No": i,
                    "Tanggal Upload": d.get("uploaded_at", ""),
                    "Nama Dokumen": d.get("title", ""),
                    "Kategori": d.get("category", ""),
                    "Tahun": d.get("year", ""),
                    "Pengupload": d.get("uploader_name", d.get("uploader_id", ""))
                })
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True)

            st.markdown("---")
            # ================= Detail per Dokumen =================
            for d in docs:
                doc_id = str(d["_id"])
                cols = st.columns([4,1,1,1])
                with cols[0]:
                    st.markdown(f"**{d.get('title')}**  \nKategori: {d.get('category')}  • Tahun: {d.get('year')}  \nUploader: {d.get('uploader_id')}  \nUploaded: {d.get('uploaded_at')}")
                    st.write(d.get("description", ""))
                with cols[1]:
                    if os.path.exists(d.get("file_path","")):
                        with open(d["file_path"], "rb") as f:
                            file_bytes = f.read()
                            st.download_button("Download", file_bytes, file_name=d.get("original_filename", "dokumen.pdf"))

                with cols[2]:
                    if (role == "admin") or (str(user["_id"]) == str(d["uploader_id"])):
                        if st.button(f"Edit", key=f"edit_{doc_id}"):
                            st.session_state[f"editing_{doc_id}"] = True
                with cols[3]:
                    if role == "admin":
                        if st.button("Hapus", key=f"hapus_{doc_id}"):
                            ok = delete_document(doc_id)
                            if ok:
                                st.success("Dokumen dihapus.")
                                st.rerun()

                with st.expander("Preview Dokumen"):
                    if os.path.exists(d.get("file_path","")):
                        preview_pdf_inline(d["file_path"], height=600)
                    else:
                        st.error("File tidak tersedia di server.")
                st.markdown("---")

    # ----------------- Pencarian -----------------
    elif choice == "Pencarian & Filter":
        st.title("Pencarian & Filter")
        q_title = st.text_input("Cari judul (substring)")
        q_cat = st.selectbox("Kategori", [""] + list_categories())
        q_year = st.text_input("Tahun (kosong = semua)")
        query = {}
        if q_title:
            query["title"] = {"$regex": q_title, "$options": "i"}
        if q_cat:
            query["category"] = q_cat
        if q_year:
            try:
                query["year"] = int(q_year)
            except:
                st.error("Format tahun salah")
        docs = list_documents(query)
        st.write(f"Hasil: {len(docs)} dokumen")
        for d in docs:
            st.write(f"**{d.get('title')}** — {d.get('category')} ({d.get('year')})")
            if os.path.exists(d.get("file_path","")):
                with open(d["file_path"], "rb") as f:
                    file_bytes = f.read()
                    st.download_button("Download", file_bytes, file_name=d.get("original_filename", "dokumen.pdf"))
            st.markdown("---")

    # ----------------- Kelola Kategori (Admin) -----------------
    elif choice == "Kelola Kategori" and role == "admin":
        st.title("Kelola Kategori")
        st.subheader("Tambah Kategori")
        new_cat = st.text_input("Nama kategori baru")
        if st.button("Tambah"):
            if not new_cat.strip():
                st.error("Nama kategori tidak boleh kosong.")
            elif add_category(new_cat.strip()):
                st.success("Kategori ditambahkan")
            else:
                st.error("Kategori sudah ada")
        st.subheader("Daftar Kategori")
        cats = list_categories()
        for c in cats:
            col1, col2 = st.columns([4,1])
            col1.write(c)
            if col2.button("Hapus", key=f"delcat_{c}"):
                remove_category(c)
                st.success("Kategori dihapus")
                st.rerun()

    # ----------------- Manajemen User (Admin) -----------------
    elif choice == "Manajemen User" and role == "admin":
        st.title("Manajemen User")
        users = list(users_col.find())
        df = pd.DataFrame([{
            "id": str(u["_id"]),
            "name": u.get("name"),
            "email": u.get("email"),
            "role": u.get("role"),
            "active": u.get("active", True),
            "created_at": u.get("created_at")
        } for u in users])
        st.dataframe(df)
        st.subheader("Buat user baru")
        cu_name = st.text_input("Nama")
        cu_email = st.text_input("Email")
        cu_pass = st.text_input("Password", type="password")
        cu_role = st.selectbox("Role", ["admin", "staf", "viewer"])
        if st.button("Buat user"):
            if not cu_name or not cu_email or not cu_pass:
                st.error("Harap isi semua field.")
            else:
                ok, msg = register_user(cu_name.strip(), cu_email.strip(), cu_pass, cu_role)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # ----------------- Logout -----------------
    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

# ---------------------------
# Routing Auth
# ---------------------------
if not st.session_state.logged_in:
    if st.session_state.auth_page == "login":
        page_login()
    elif st.session_state.auth_page == "register":
        page_register()
else:
    page_dashboard()
