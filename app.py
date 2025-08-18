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
import os, base64

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
    if os.path.exists("logo_kpu.png"):
        with open("logo_kpu.png", "rb") as f:
            data = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <div style="text-align: center;">
                <img src="data:image/png;base64,{data}" width="120">
                <h2 style='color:#B22222;'>Aplikasi Arsip KPU Kota Surabaya</h2>
                <p style='font-size:16px;'>Selamat datang di aplikasi digitalisasi arsip KPU</p>
            </div>
            """,
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

    menu_items = ["Dashboard", "Lihat Arsip", "Pencarian & Filter",  "Upload Dokumen",  "Kelola Dokumen Anda", "Profil"]
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

    # ----------------- Profil -----------------
    elif choice == "Profil":
        st.title("Profil Pengguna")
        st.write(f"**Nama**: {user['name']}")
        st.write(f"**Email**: {user['email']}")
        st.write(f"**Role**: {user['role']}")
        st.write(f"**Dibuat pada**: {user.get('created_at', 'N/A')}")

    # ----------------- Kelola Dokumen Anda -----------------
    elif choice == "Kelola Dokumen Anda":
        st.title("Dokumen Anda")
        docs = list_documents({"uploader_id": user["_id"]})
        if not docs:
            st.info("Anda belum mengupload dokumen.")
        else:
            for d in docs:
                doc_id = str(d["_id"])
                st.markdown(f"### {d.get('title')}")
                st.write(f"Kategori: {d.get('category')}  • Tahun: {d.get('year')}")
                st.write(f"Deskripsi: {d.get('description', '')}")
                st.write(f"Uploaded: {d.get('uploaded_at')}")

                # ---- Tombol aksi ----
                col1, col2, col3, col4 = st.columns([1,1,1,1])
                with col1:
                    if os.path.exists(d.get("file_path","")):
                        with open(d["file_path"], "rb") as f:
                            file_bytes = f.read()
                            st.download_button("Download", file_bytes, file_name=d.get("original_filename", "dokumen.pdf"), key=f"dl_{doc_id}")
                with col2:
                    with st.expander("Preview Dokumen"):
                        if os.path.exists(d.get("file_path","")):
                            preview_pdf_inline(d["file_path"], height=400)
                with col3:
                    if st.button("Edit Metadata", key=f"edit_{doc_id}"):
                        st.session_state[f"editing_{doc_id}"] = True
                        st.rerun()
                with col4:
                    if st.button("Hapus", key=f"hapus_self_{doc_id}"):
                        ok = delete_document(doc_id)
                        if ok:
                            st.success("Dokumen dihapus.")
                            st.rerun()
                # ---- Form Edit Metadata ----
                if st.session_state.get(f"editing_{doc_id}", False):
                    st.subheader("Edit Metadata")
                    new_title = st.text_input("Judul", value=d.get("title",""), key=f"title_{doc_id}")
                    new_desc = st.text_area("Deskripsi", value=d.get("description",""), key=f"desc_{doc_id}")
                    new_cat = st.selectbox("Kategori", list_categories(), index=list_categories().index(d.get("category")) if d.get("category") in list_categories() else 0, key=f"cat_{doc_id}")
                    new_year = st.number_input("Tahun", min_value=1900, max_value=2100, value=int(d.get("year", datetime.utcnow().year)), key=f"year_{doc_id}")
                    if st.button("Simpan", key=f"simpan_{doc_id}"):
                        ok = update_metadata(doc_id, {
                            "title": new_title.strip(),
                            "description": new_desc.strip(),
                            "category": new_cat,
                            "year": int(new_year)
                        })
                        if ok:
                            st.success("Metadata diperbarui.")
                            st.session_state[f"editing_{doc_id}"] = False
                            st.rerun()
                    if st.button("Batal", key=f"batal_{doc_id}"):
                        st.session_state[f"editing_{doc_id}"] = False
                        st.rerun()

                st.markdown("---")

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
    elif choice == "Lihat Arsip":
        st.title("Daftar Dokumen")
        docs = list_documents()
        if not docs:
            st.info("Belum ada dokumen.")
        else:
            # mapping user id -> nama
            user_map = {str(u["_id"]): u.get("name", "Unknown") for u in users_col.find()}

            st.subheader("📑 Tabel Daftar Dokumen")
            table_data = []
            for i, d in enumerate(docs, start=1):
                uploader_name = user_map.get(str(d.get("uploader_id")), d.get("uploader_id"))
                table_data.append({
                    "No": i,
                    "Tanggal Upload": d.get("uploaded_at", ""),
                    "Nama Dokumen": d.get("title", ""),
                    "Kategori": d.get("category", ""),
                    "Tahun": d.get("year", ""),
                    "Pengupload": uploader_name
                })
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True)

            st.markdown("---")
            for d in docs:
                doc_id = str(d["_id"])
                uploader_name = user_map.get(str(d.get("uploader_id")), d.get("uploader_id"))

                cols = st.columns([4,1,1,1])
                with cols[0]:
                    st.markdown(
                        f"**{d.get('title')}**  \n"
                        f"Kategori: {d.get('category')}  • Tahun: {d.get('year')}  \n"
                        f"Uploader: {uploader_name}  \n"
                        f"Uploaded: {d.get('uploaded_at')}"
                    )
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
