import streamlit as st
import requests
import pandas as pd
import gspread
import math
import time
import io
import datetime
import base64
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from streamlit_paste_button import paste_image_button
WIB = datetime.timezone(datetime.timedelta(hours=7))

# --- 1. INISIALISASI SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_username = ""
    st.session_state.user_nama_ic = ""
    st.session_state.user_jabatan = ""

# --- 2. KONEKSI GOOGLE (SHEETS & DRIVE) ---
# --- 2. KONEKSI GOOGLE (SHEETS & DRIVE) ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    # 1. Mengambil data dari Secrets Streamlit
    # Pastikan di menu Secrets kamu sudah pakai label [my_google_creds]
    creds_dict = st.secrets["my_google_creds"]
    
    # 2. Inisialisasi Kredensial
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    # 3. Inisialisasi Client
    client = gspread.authorize(creds)
    
    # 4. Hubungkan ke Spreadsheet (ID tetap sama)
    ID_SHEET = "1e28VoHNGJVVnEsSBVA7Plt03C9gaBSo6gRE6QYKRKko"
    
    # 5. Hubungkan ke tiap Worksheet
    sheet = client.open_by_key(ID_SHEET).sheet1
    sheet_farmasi = client.open_by_key(ID_SHEET).worksheet("Penjualan_Farmasi")
    sheet_absen = client.open_by_key(ID_SHEET).worksheet("Absensi")
    sheet_user = client.open_by_key(ID_SHEET).worksheet("Database_User")
    
    # Coba hubungkan Log, jika belum ada buat dulu di Google Sheets
    try:
        sheet_log = client.open_by_key(ID_SHEET).worksheet("Log_Aktivitas")
    except:
        st.error("⚠️ Sheet 'Log_Aktivitas' tidak ditemukan! Buat dulu di Google Sheets kamu.")

except Exception as e:
    # Ini yang memunculkan pesan kuning di gambar kamu jika ada error di atas
    st.warning(f"⚠️ Koneksi Gagal: {e}")

# Fungsi Global untuk mencatat log (Letakkan tepat setelah blok try-except)
def catat_log(aktivitas, detail="-"):
    try:
        ts = datetime.datetime.now(WIB).strftime("%d/%m/%Y %H:%M:%S")
        username = st.session_state.get('user_username', 'GUEST')
        nama_ic = st.session_state.get('user_nama_ic', 'GUEST')
        # Gunakan variabel sheet_log yang sudah dikoneksikan di atas
        sheet_log.append_row([ts, username, nama_ic, aktivitas, detail])
    except:
        pass

# --- 3. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="EMS SIXNINE MEDICAL CENTRE", layout="wide", page_icon="🚑")

def get_base64(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

bg = get_base64('ems_front.png')

# ── MASTER CSS ────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=Sora:wght@600;700;800&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after {{ box-sizing: border-box; }}

.stApp {{
    background:
        linear-gradient(160deg, rgba(4,6,18,0.97) 0%, rgba(8,14,36,0.95) 60%, rgba(4,6,18,0.97) 100%),
        url("data:image/png;base64,{bg}");
    background-size: cover;
    background-attachment: fixed;
    font-family: 'DM Sans', sans-serif;
    color: #e2e8f0;
}}

/* ── Streamlit Header ── */
header[data-testid="stHeader"] {{
    background: rgba(4, 6, 18, 0.85) !important;
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(99,179,237,0.08);
}}

/* ── Hide default decoration ── */
#MainMenu, footer {{ visibility: hidden; }}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: rgba(8, 14, 36, 0.92) !important;
    border-right: 1px solid rgba(99,179,237,0.10) !important;
    backdrop-filter: blur(24px);
}}
[data-testid="stSidebar"] .block-container {{ padding: 2rem 1.4rem; }}

/* Radio nav */
[data-testid="stSidebar"] .stRadio label {{
    display: block;
    padding: 0.55rem 1rem;
    border-radius: 10px;
    font-size: 0.82rem;
    font-weight: 500;
    letter-spacing: 0.05em;
    color: #94a3b8;
    transition: background 0.18s, color 0.18s;
    cursor: pointer;
}}
[data-testid="stSidebar"] .stRadio label:hover {{
    background: rgba(99,179,237,0.08);
    color: #e2e8f0;
}}
[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label,
[data-testid="stSidebar"] .stRadio input:checked + label {{
    background: rgba(56,189,248,0.12);
    color: #7dd3fc;
}}

/* ── Profile Card ── */
.profile-card {{
    background: linear-gradient(135deg, rgba(56,189,248,0.07), rgba(99,102,241,0.07));
    border: 1px solid rgba(56,189,248,0.15);
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
    margin-bottom: 1.8rem;
}}
.profile-card .label {{
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    color: #64748b;
    text-transform: uppercase;
    margin: 0 0 0.3rem;
}}
.profile-card .name {{
    font-family: 'Sora', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0;
}}
.profile-card .badge {{
    display: inline-block;
    margin-top: 0.45rem;
    padding: 0.2rem 0.75rem;
    border-radius: 99px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    background: rgba(56,189,248,0.12);
    color: #38bdf8;
    border: 1px solid rgba(56,189,248,0.2);
    text-transform: uppercase;
}}

/* ── Page Titles ── */
.page-title {{
    font-family: 'Sora', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
    color: #f1f5f9;
    letter-spacing: -0.02em;
    margin-bottom: 0.25rem;
    line-height: 1.2;
}}
.page-subtitle {{
    font-size: 0.85rem;
    color: #64748b;
    margin-bottom: 2rem;
    letter-spacing: 0.02em;
}}
.title-accent {{
    color: #38bdf8;
}}

/* ── Cards & Containers ── */
.card {{
    background: rgba(15, 23, 50, 0.7);
    border: 1px solid rgba(99,179,237,0.10);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    backdrop-filter: blur(12px);
}}
.info-pill {{
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(56,189,248,0.08);
    border: 1px solid rgba(56,189,248,0.15);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    font-size: 0.83rem;
    color: #7dd3fc;
    margin-bottom: 1.2rem;
}}
.status-on {{
    background: rgba(16,185,129,0.08);
    border: 1px solid rgba(16,185,129,0.18);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    color: #6ee7b7;
    font-size: 0.88rem;
    line-height: 1.7;
    margin-bottom: 1rem;
}}
.status-off {{
    background: rgba(239,68,68,0.06);
    border: 1px solid rgba(239,68,68,0.14);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    color: #fca5a5;
    font-size: 0.88rem;
    margin-bottom: 1rem;
}}
.week-info {{
    background: linear-gradient(90deg, rgba(56,189,248,0.06), rgba(99,102,241,0.06));
    border: 1px solid rgba(56,189,248,0.12);
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    font-size: 0.85rem;
    color: #94a3b8;
}}
.week-info strong {{ color: #fbbf24; }}

/* ── Login Page ── */
.login-wrap {{
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 3rem 0 1rem;
}}
.login-brand {{
    font-family: 'Sora', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: #f1f5f9;
    letter-spacing: -0.02em;
    text-align: center;
    margin-top: 1rem;
}}
.login-brand span {{ color: #38bdf8; }}
.login-tagline {{
    font-size: 0.78rem;
    color: #475569;
    text-align: center;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 2rem;
}}

/* ── Streamlit Inputs ── */
.stTextInput input, .stSelectbox select, .stDateInput input, .stNumberInput input {{
    background: rgba(15, 23, 50, 0.8) !important;
    border: 1px solid rgba(99,179,237,0.14) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
}}
.stTextInput input:focus, .stSelectbox select:focus {{
    border-color: rgba(56,189,248,0.4) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,0.08) !important;
}}
.stTextInput label, .stSelectbox label, .stDateInput label,
.stNumberInput label, .stFileUploader label {{
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #64748b !important;
}}

/* ── Buttons ── */
.stButton > button {{
    background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.55rem 1.4rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    transition: opacity 0.18s, transform 0.12s !important;
    box-shadow: 0 4px 14px rgba(56,189,248,0.18) !important;
}}
.stButton > button:hover {{
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}}
.stButton > button:active {{
    transform: translateY(0) !important;
}}

/* ── Form submit button ── */
.stFormSubmitButton > button {{
    background: linear-gradient(135deg, #0ea5e9, #6366f1) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    box-shadow: 0 4px 14px rgba(56,189,248,0.18) !important;
    transition: opacity 0.18s, transform 0.12s !important;
}}
.stFormSubmitButton > button:hover {{
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    background: rgba(8,14,36,0.6);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(99,179,237,0.08);
    gap: 2px;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 9px;
    color: #64748b;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 0.45rem 1rem;
    border: none !important;
    transition: all 0.18s;
}}
.stTabs [aria-selected="true"] {{
    background: rgba(56,189,248,0.12) !important;
    color: #38bdf8 !important;
}}

/* ── Alerts ── */
.stSuccess, .stError, .stWarning, .stInfo {{
    border-radius: 12px !important;
    font-size: 0.85rem !important;
    border-left-width: 3px !important;
}}

/* ── Dataframe ── */
.stDataFrame {{
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(99,179,237,0.10) !important;
}}

/* ── Divider ── */
hr {{
    border-color: rgba(99,179,237,0.08) !important;
    margin: 1.5rem 0 !important;
}}

/* ── Expander ── */
.streamlit-expanderHeader {{
    background: rgba(15,23,50,0.6) !important;
    border-radius: 10px !important;
    font-size: 0.83rem !important;
    color: #94a3b8 !important;
}}

/* ── Logout button in sidebar ── */
[data-testid="stSidebar"] .stButton > button {{
    background: rgba(239,68,68,0.08) !important;
    border: 1px solid rgba(239,68,68,0.16) !important;
    color: #fca5a5 !important;
    box-shadow: none !important;
    width: 100%;
}}
[data-testid="stSidebar"] .stButton > button:hover {{
    background: rgba(239,68,68,0.15) !important;
}}

/* ── Home ── */
.home-hero {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 6vh 2rem 4vh;
    text-align: center;
}}
.home-hero .hero-title {{
    font-family: 'Sora', sans-serif;
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    font-weight: 800;
    color: #f1f5f9;
    letter-spacing: -0.03em;
    line-height: 1.05;
    margin: 1.5rem 0 0.5rem;
}}
.home-hero .hero-title span {{ color: #38bdf8; }}
.home-hero .hero-sub {{
    font-size: 0.88rem;
    color: #475569;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 0.8rem;
}}
.home-divider {{
    width: 60px;
    height: 2px;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    border-radius: 2px;
    margin: 1.5rem auto 0;
}}

/* Total highlight */
.total-box {{
    background: linear-gradient(135deg, rgba(56,189,248,0.07), rgba(99,102,241,0.07));
    border: 1px solid rgba(56,189,248,0.15);
    border-radius: 12px;
    padding: 1rem 1.4rem;
    text-align: center;
    margin-top: 1rem;
}}
.total-box h3 {{
    font-family: 'Sora', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #7dd3fc;
    margin: 0;
}}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 4. LOGIN & DAFTAR
# ─────────────────────────────────────────────────────────────────────────────
LIST_JABATAN_DAFTAR = ["TRAINEE", "CO-ASS", "DOKTER UMUM", "DOKTER SPESIALIS", "ADMINISTRASI & KEUANGAN", "BENDAHARA", "SEKRETARIS", "SDM - KOMDIS", "SDM - FTO", "WAKIL DIREKTUR", "DIREKTUR", "CEO"]
LIST_JABATAN_FULL = LIST_JABATAN_DAFTAR + ["ADMIN"]

if not st.session_state.logged_in:
    # Logo & brand
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        st.image('ems69_logo.png', width=110, use_container_width=False, output_format="PNG")
        st.markdown('<p class="login-brand">SIXNINE <span>MEDICAL</span> CENTRE</p>', unsafe_allow_html=True)
        st.markdown('<p class="login-tagline">Emergency Medical Services · Management System</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        t_login, t_daftar = st.tabs(["  Masuk  ", "  Daftar  "])

        with t_login:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("form_login"):
                in_user = st.text_input("Username")
                in_pass = st.text_input("Password", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Masuk", use_container_width=True):
                    if in_user == "emsadmin" and in_pass == "ems@sixnine#admin123":
                        st.session_state.logged_in = True
                        st.session_state.user_username = "emsadmin"
                        st.session_state.user_nama_ic = "ADMIN EMS"
                        st.session_state.user_jabatan = "ADMIN"
                        catat_log("LOGIN", "Master Admin Login")
                        st.rerun()
                    else:
                        users_data = sheet_user.get_all_records()
                        user_found = next((u for u in users_data if str(u['Username']) == in_user and str(u['Password']) == in_pass), None)
                        if user_found:
                            st.session_state.logged_in = True
                            st.session_state.user_username = user_found['Username']
                            st.session_state.user_nama_ic = user_found['Nama_IC']
                            st.session_state.user_jabatan = user_found['Jabatan']
                            catat_log("LOGIN", "User Login Berhasil")
                            st.rerun()
                        else:
                            st.error("Username atau password salah.")

        with t_daftar:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("form_reg"):
                reg_user = st.text_input("Username (untuk login)")
                reg_nama_ic = st.text_input("Nama IC (nama karakter)")
                reg_pass = st.text_input("Password", type="password")
                reg_jabatan = st.selectbox("Jabatan", LIST_JABATAN_DAFTAR)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("Buat Akun", use_container_width=True):
                    if reg_user and reg_nama_ic and reg_pass:
                        users = sheet_user.get_all_records()
                        if any(u['Username'] == reg_user for u in users) or reg_user == "emsadmin":
                            st.error("Username sudah terdaftar.")
                        else:
                            ts = datetime.datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
                            sheet_user.append_row([ts, reg_user, reg_nama_ic.upper(), reg_pass, reg_jabatan])
                            catat_log("DAFTAR AKUN", f"User baru mendaftar: {reg_nama_ic.upper()} sebagai {reg_jabatan}")
                            st.success("Akun berhasil dibuat! Silakan masuk.")
                    else:
                        st.error("Lengkapi semua data.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 5. SIDEBAR & NAVIGASI
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.markdown(f"""
<div class="profile-card">
    <p class="label">Operator</p>
    <p class="name">👤 {st.session_state.user_nama_ic}</p>
    <span class="badge">🔰 {st.session_state.user_jabatan}</span>
</div>
""", unsafe_allow_html=True)

role = st.session_state.user_jabatan
opsi_menu = ["HOME", "ABSENSI"]
if role != "TRAINEE":
    opsi_menu.append("PEMBUATAN KTS")
farmasi_access = ["DOKTER UMUM", "DOKTER SPESIALIS", "ADMINISTRASI & KEUANGAN", "BENDAHARA", "SEKRETARIS", "SDM - KOMDIS", "SDM - FTO", "WAKIL DIREKTUR", "DIREKTUR", "CEO", "ADMIN"]
if role in farmasi_access:
    opsi_menu.append("PENJUALAN FARMASI")
admin_panel_access = ["SDM - KOMDIS", "SDM - FTO", "WAKIL DIREKTUR", "DIREKTUR", "CEO", "ADMIN"]
if role in admin_panel_access:
    opsi_menu.append("ADMIN MENU")

menu = st.sidebar.radio("Navigasi", opsi_menu)
st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("Logout"):
    catat_log("LOGOUT", "User keluar dari sistem")
    st.session_state.logged_in = False
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 6. KONTEN
# ─────────────────────────────────────────────────────────────────────────────

# ── HOME ──────────────────────────────────────────────────────────────────────
if menu == "HOME":
    st.markdown('<div class="home-hero">', unsafe_allow_html=True)
    st.image('ems69_logo.png', width=120, use_container_width=False, output_format="PNG")
    st.markdown("""
        <h1 class="hero-title">Welcome to EMS<br><span>Sixnine Medical</span></h1>
        <p class="hero-sub">Emergency Medical Services · Management System</p>
        <div class="home-divider"></div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── PEMBUATAN KTS ──────────────────────────────────────────────────────────────
elif menu == "PEMBUATAN KTS":
    st.markdown('<p class="page-title">📝 Kartu Tanda <span class="title-accent">Sehat</span></p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Pembuatan & perpanjangan KTS warga</p>', unsafe_allow_html=True)

    if 'form_reset_counter' not in st.session_state:
        st.session_state.form_reset_counter = 0
    suffix = str(st.session_state.form_reset_counter)
    tgl_buat = datetime.date.today()
    tgl_exp = tgl_buat + datetime.timedelta(days=30)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**🆔 Identitas KTP**")
        p_ktp = paste_image_button(label="📋 Paste KTP (Ctrl+V)", key=f"p_ktp_{suffix}")
        f_ktp = st.file_uploader("Atau upload KTP", type=['png','jpg','jpeg'], key=f"f_ktp_{suffix}")
        if p_ktp.image_data:
            st.session_state.img_ktp_final = p_ktp.image_data
        elif f_ktp:
            st.session_state.img_ktp_final = f_ktp
        if st.session_state.get('img_ktp_final'):
            st.image(st.session_state.img_ktp_final, width=280)

        st.markdown("<br>**👤 Pas Foto**", unsafe_allow_html=True)
        link_pas_foto = st.text_input("🔗 Link foto (ShareX / screenshot)", placeholder="https://...", key=f"link_pas_{suffix}")
        p_pas = paste_image_button(label="📋 Paste Foto", key=f"p_pas_{suffix}")
        f_pas = st.file_uploader("Atau upload file", type=['png','jpg','jpeg'], key=f"f_pas_{suffix}")
        if link_pas_foto:
            st.session_state.img_pas_final = link_pas_foto
        elif p_pas.image_data:
            st.session_state.img_pas_final = p_pas.image_data
        elif f_pas:
            st.session_state.img_pas_final = f_pas
        if st.session_state.get('img_pas_final'):
            st.image(st.session_state.img_pas_final, width=280)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("**📋 Data Pasien**")
        with st.form(key=f"kts_form_{suffix}"):
            nama = st.text_input("Nama Lengkap")
            tgl_lahir = st.date_input("Tanggal Lahir", value=datetime.date(2000, 1, 1))
            jk = st.selectbox("Jenis Kelamin", ["LAKI-LAKI", "PEREMPUAN"])
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("💾 Simpan ke Database", use_container_width=True):
                if nama and st.session_state.get('img_ktp_final') and st.session_state.get('img_pas_final'):
                    try:
                        with st.spinner("Memproses..."):
                            WEBHOOK_URL = "https://discord.com/api/webhooks/1487193498556829938/cWeI5termckSlCK4ssmCVW04DJRXwxsacrFR0VGgpjhAOwQcCWV36KRmn-z9OScrDTKH"
                            def upload_to_discord(img_source, filename):
                                if isinstance(img_source, str):
                                    response_img = requests.get(img_source)
                                    file_bytes = response_img.content
                                else:
                                    if hasattr(img_source, 'getvalue'):
                                        file_bytes = img_source.getvalue()
                                    else:
                                        buf = io.BytesIO()
                                        img_source.save(buf, format='PNG')
                                        file_bytes = buf.getvalue()
                                files = {'file': (f"{filename}_{nama}.png", file_bytes)}
                                r = requests.post(WEBHOOK_URL, data={"content": f"📢 **KTS Update/Baru: {nama.upper()}**"}, files=files)
                                return r.json()['attachments'][0]['url'] if r.status_code == 200 else "Gagal"

                            url_ktp = upload_to_discord(st.session_state.img_ktp_final, "KTP")
                            sumber_pas = st.session_state.img_pas_final
                            url_pas_discord = upload_to_discord(sumber_pas, "PASFOTO")
                            url_simpan_sheets = sumber_pas if isinstance(sumber_pas, str) else url_pas_discord
                            ts = datetime.datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
                            data_baru = [ts, nama.upper(), str(tgl_lahir), jk, url_ktp, url_simpan_sheets, tgl_exp.strftime("%d/%m/%Y"), st.session_state.user_nama_ic]

                            found_cell = None
                            try:
                                found_cell = sheet.find(nama.upper())
                            except:
                                found_cell = None

                            if found_cell:
                                sheet.update(f"A{found_cell.row}:H{found_cell.row}", [data_baru])
                                catat_log("PERPANJANG KTS", f"Memperbarui KTS pasien: {nama.upper()}")
                                st.success(f"✅ KTS diperbarui untuk {nama.upper()}")
                            else:
                                sheet.append_row(data_baru)
                                catat_log("BUAT KTS BARU", f"Mendaftarkan pasien baru: {nama.upper()}")
                                st.success(f"✅ KTS baru berhasil disimpan untuk {nama.upper()}")

                            st.balloons()
                            st.session_state.img_ktp_final = None
                            st.session_state.img_pas_final = None
                            st.session_state.form_reset_counter += 1
                            time.sleep(2)
                            st.rerun()
                    except Exception as err:
                        st.error(f"Terjadi kesalahan: {err}")
                else:
                    st.error("Data belum lengkap. Lengkapi semua field dan gambar.")
        st.markdown('</div>', unsafe_allow_html=True)

# ── PENJUALAN FARMASI ──────────────────────────────────────────────────────────
elif menu == "PENJUALAN FARMASI":
    st.markdown('<p class="page-title">💊 Penjualan <span class="title-accent">Farmasi</span></p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Sistem penjualan obat & peralatan medis</p>', unsafe_allow_html=True)

    try:
        data_kts_for_farmasi = sheet.get_all_records()
        list_nama_warga = sorted(list(set([str(row['Nama']).upper() for row in data_kts_for_farmasi])))
    except:
        list_nama_warga = []

    now = datetime.datetime.now(WIB)
    hari_efektif = (now - datetime.timedelta(days=1)).strftime("%d/%m/%Y") if now.hour < 13 else now.strftime("%d/%m/%Y")
    st.markdown(f'<div class="info-pill">📅 Tanggal sesi penjualan: <strong>{hari_efektif}</strong></div>', unsafe_allow_html=True)

    with st.form("form_farmasi_v2"):
        f_nama_pilihan = st.selectbox("Pilih Nama", options=["-- Manual --"] + list_nama_warga)
        f_nama_manual = st.text_input("Nama Manual (jika tidak ada di daftar)")
        nama_final = f_nama_pilihan if f_nama_pilihan != "-- Manual --" else f_nama_manual
        is_warga = f_nama_pilihan != "-- Manual --"
        c1, c2 = st.columns(2)
        f_item = c1.selectbox("Item", ["Medic Bag", "Medic Pouch", "Perban", "Aprazolam"])
        f_qty = c2.number_input("Jumlah", min_value=1, value=1)
        harga_map = {"Medic Bag": 300, "Medic Pouch": 200, "Perban": 35, "Aprazolam": 35}
        total_bayar = harga_map[f_item] * f_qty
        st.markdown(f'<div class="info-pill">💰 Total: <strong>${total_bayar:,}</strong></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("✅ Proses Pembayaran", use_container_width=True):
            if not nama_final:
                st.error("Nama harus diisi.")
            else:
                try:
                    boleh_beli, msg = True, ""
                    if is_warga:
                        records = sheet_farmasi.get_all_records()
                        today_sales = sum(r['Jumlah'] for r in records if r['Nama Pasien'].strip().upper() == nama_final.strip().upper() and str(r['Timestamp']).split(' ')[0] == hari_efektif and r['Item/Obat'] == f_item)
                        if f_item == "Medic Bag" and today_sales + f_qty > 1:
                            boleh_beli, msg = False, "Limit Medic Bag sudah habis untuk hari ini."
                        elif f_item == "Medic Pouch" and today_sales + f_qty > 2:
                            boleh_beli, msg = False, "Limit Medic Pouch sudah habis untuk hari ini."

                    if boleh_beli:
                        sheet_farmasi.append_row([now.strftime("%d/%m/%Y %H:%M"), nama_final.upper(), f_item, harga_map[f_item], f_qty, total_bayar, st.session_state.user_nama_ic])
                        catat_log("PENJUALAN FARMASI", f"Menjual {f_qty}x {f_item} ke {nama_final.upper()}")
                        st.success("✅ Transaksi berhasil!")
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Transaksi ditolak: {msg}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ── ABSENSI ────────────────────────────────────────────────────────────────────
elif menu == "ABSENSI":
    st.markdown('<p class="page-title">🕒 Sistem <span class="title-accent">On/Off Duty</span></p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Manajemen absensi dan riwayat kehadiran</p>', unsafe_allow_html=True)

    tgl_mulai_kota = datetime.datetime(2026, 1, 19)

    def get_info_minggu(tgl_obj):
        if isinstance(tgl_obj, datetime.datetime):
            tgl_obj = tgl_obj.date()
        selisih_hari = (tgl_obj - tgl_mulai_kota.date()).days
        minggu_ke = (selisih_hari // 7) + 1
        senin = tgl_obj - datetime.timedelta(days=tgl_obj.weekday())
        minggu = senin + datetime.timedelta(days=6)
        periode_str = f"{senin.strftime('%d %b')} – {minggu.strftime('%d %b %Y')}"
        return int(minggu_ke), periode_str

    def simpan_absen_smart(dt_on, dt_off, mode="Otomatis", ket=""):
        try:
            m_ke, periode_str = get_info_minggu(dt_on)
            durasi = dt_off - dt_on
            total_detik = int(durasi.total_seconds())
            if total_detik < 0:
                total_detik = 0
            jam, sisa = divmod(total_detik, 3600)
            menit, _ = divmod(sisa, 60)
            durasi_str = f"{jam} jam {menit} menit"
            sheet_absen.append_row([
                st.session_state.user_nama_ic,
                st.session_state.user_jabatan,
                dt_on.strftime("%d/%m/%Y"),
                dt_on.strftime("%H:%M"),
                dt_off.strftime("%H:%M"),
                durasi_str, m_ke,
                f"{mode}: {ket}" if ket else mode,
                periode_str
            ])
            return True, durasi_str
        except Exception as e:
            return False, str(e)

    m_sekarang, p_sekarang = get_info_minggu(datetime.datetime.now(WIB))
    st.markdown(f"""
        <div class="week-info">
            Periode aktif: <strong>{p_sekarang}</strong> &nbsp;·&nbsp; Minggu ke-{m_sekarang}
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["⚡ Real-time", "📝 Input Manual", "📊 Riwayat Saya"])

    with tab1:
        is_on_duty = st.session_state.get('waktu_on_raw') is not None

        if not is_on_duty:
            st.markdown('<div class="status-off">🔴 Status Anda saat ini: <strong>OFF DUTY</strong></div>', unsafe_allow_html=True)
            if st.button("🚀 Mulai On Duty Sekarang", use_container_width=True):
                st.session_state.waktu_on_raw = datetime.datetime.now(WIB)
                st.success(f"Status: 🟢 ON DUTY · Pukul {st.session_state.waktu_on_raw.strftime('%H:%M:%S')}")
                st.rerun()
        else:
            waktu_on = st.session_state.waktu_on_raw
            waktu_sekarang = datetime.datetime.now(WIB)
            durasi_berjalan = waktu_sekarang - waktu_on
            jam_berjalan, sisa_berjalan = divmod(int(durasi_berjalan.total_seconds()), 3600)
            st.markdown(f"""
                <div class="status-on">
                    🟢 Status: <strong>ON DUTY</strong><br>
                    Mulai pukul: {waktu_on.strftime('%H:%M:%S')}<br>
                    Durasi berjalan: {jam_berjalan} jam {sisa_berjalan // 60} menit
                </div>
            """, unsafe_allow_html=True)
            st.divider()
            with st.form("form_off_duty"):
                f_keterangan_on = st.text_input("Keterangan kegiatan (opsional)", placeholder="Contoh: Patroli, Jaga RS")
                if st.form_submit_button("🛑 Selesai & Off Duty", use_container_width=True):
                    with st.spinner("Menghitung durasi dan menyimpan..."):
                        tgl_selesai = datetime.datetime.now(WIB)
                        sukses, durasi_total = simpan_absen_smart(waktu_on, tgl_selesai, "Real-time", f_keterangan_on)
                        if sukses:
                            st.balloons()
                            del st.session_state.waktu_on_raw
                            st.success(f"✅ Off Duty berhasil! Durasi sesi: **{durasi_total}**")
                            time.sleep(3)
                            st.rerun()
                        else:
                            st.error(f"Gagal menyimpan: {durasi_total}")

    with tab2:
        st.markdown("**📝 Input Absensi Manual**")
        st.caption("Gunakan form ini jika lupa absen real-time.")
        with st.form("absen_manual_form"):
            m_tgl = st.date_input("Tanggal Kegiatan", value=datetime.date.today())
            c1, c2 = st.columns(2)
            m_on = c1.text_input("Jam Mulai (HH:MM)", "20:00", placeholder="HH:MM")
            m_off = c2.text_input("Jam Selesai (HH:MM)", "22:00", placeholder="HH:MM")
            m_ket = st.text_input("Keterangan / Alasan Manual", placeholder="Contoh: Lupa absen, Patroli Kota")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("💾 Simpan Absen Manual", use_container_width=True):
                if m_on and m_off and m_ket:
                    try:
                        dt_on_manual = datetime.datetime.combine(m_tgl, datetime.datetime.strptime(m_on, "%H:%M").time())
                        dt_off_manual = datetime.datetime.combine(m_tgl, datetime.datetime.strptime(m_off, "%H:%M").time())
                        if dt_off_manual <= dt_on_manual:
                            dt_off_manual += datetime.timedelta(days=1)
                        sukses, durasi_manual = simpan_absen_smart(dt_on_manual, dt_off_manual, "Manual (Koreksi)", m_ket)
                        if sukses:
                            st.success(f"✅ Absen manual berhasil! Durasi: **{durasi_manual}**")
                            st.balloons()
                        else:
                            st.error(f"Gagal menyimpan: {durasi_manual}")
                    except ValueError:
                        st.error("Format jam salah! Gunakan format HH:MM (contoh: 08:30)")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan: {e}")
                else:
                    st.error("Semua field wajib diisi.")

    with tab3:
        if st.button("🔄 Refresh Data"):
            st.rerun()
        try:
            data_r = sheet_absen.get_all_records()
            if data_r:
                df_abs = pd.DataFrame(data_r)
                df_abs.columns = df_abs.columns.str.strip()
                if 'NAMA' in df_abs.columns:
                    nama_login = str(st.session_state.user_nama_ic).strip().upper()
                    df_mine = df_abs[df_abs['NAMA'].astype(str).str.strip().str.upper() == nama_login]
                    if not df_mine.empty:
                        st.dataframe(df_mine.iloc[::-1], use_container_width=True, hide_index=True)
                    else:
                        st.info(f"Belum ada riwayat absensi untuk: {st.session_state.user_nama_ic}")
                else:
                    st.error("Kolom 'NAMA' tidak ditemukan di Google Sheets.")
            else:
                st.info("Database absensi masih kosong.")
        except Exception as e:
            st.error(f"Gagal memproses data: {e}")

# ── ADMIN MENU ─────────────────────────────────────────────────────────────────
elif menu == "ADMIN MENU":
    st.markdown('<p class="page-title">⚙️ Admin <span class="title-accent">Dashboard</span></p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Manajemen karyawan, jam duty, dan log aktivitas</p>', unsafe_allow_html=True)

    if st.session_state.user_username == "emsadmin":
        with st.expander("🔐 Pengaturan Keamanan"):
            new_pass = st.text_input("Password Baru Admin", type="password")
            if st.button("Simpan Password"):
                catat_log("UBAH PASSWORD", "Master Admin mengubah password sistem")
                st.success("Password berhasil diperbarui untuk sesi ini.")

    tab_karyawan, tab_jam_duty, tab_logs = st.tabs(["👥 Karyawan", "📊 Jam Duty", "📋 Log Aktivitas"])

    with tab_karyawan:
        try:
            raw = sheet_user.get_all_values()
            df_user = pd.DataFrame(raw[1:], columns=raw[0])
            st.dataframe(df_user[['Username', 'Nama_IC', 'Jabatan']], use_container_width=True)
            st.divider()
            c_edit, c_del = st.columns(2)
            df_filt = df_user[df_user['Username'] != "emsadmin"]
            list_disp = (df_filt['Nama_IC'] + " (" + df_filt['Username'] + ")").tolist()
            with c_edit:
                st.markdown("**✏️ Edit Jabatan**")
                sel = st.selectbox("Pilih Karyawan", list_disp, key="edit")
                n_role = st.selectbox("Jabatan Baru", LIST_JABATAN_FULL)
                if st.button("Update Jabatan"):
                    u = sel.split("(")[-1].replace(")", "")
                    sheet_user.update_cell(sheet_user.find(u).row, 5, n_role)
                    catat_log("EDIT JABATAN", f"Mengubah jabatan {sel} menjadi {n_role}")
                    st.success("Jabatan berhasil diperbarui.")
                    time.sleep(1)
                    st.rerun()
            with c_del:
                st.markdown("**🗑️ Hapus Karyawan**")
                sel_d = st.selectbox("Pilih Karyawan", list_disp, key="del")
                if st.button("Hapus Akun", type="primary"):
                    u_d = sel_d.split("(")[-1].replace(")", "")
                    sheet_user.delete_rows(sheet_user.find(u_d).row)
                    catat_log("PECAT KARYAWAN", f"Menghapus akun: {sel_d}")
                    st.success("Akun berhasil dihapus.")
                    time.sleep(1)
                    st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_jam_duty:
        try:
            data_all = sheet_absen.get_all_records()
            if data_all:
                df_all = pd.DataFrame(data_all)
                df_all.columns = df_all.columns.str.strip()
                c1, c2 = st.columns(2)
                f_n = c1.selectbox("Filter Nama", ["SEMUA"] + sorted(df_all['NAMA'].unique().tolist()))
                f_m = c2.selectbox("Filter Minggu", ["SEMUA"] + sorted(df_all['MINGGU KE-'].unique().tolist()))
                df_res = df_all.copy()
                if f_n != "SEMUA":
                    df_res = df_res[df_res['NAMA'] == f_n]
                if f_m != "SEMUA":
                    df_res = df_res[df_res['MINGGU KE-'] == f_m]
                st.dataframe(df_res, use_container_width=True, hide_index=True)

                def hitung_menit(dur_str):
                    try:
                        dur_str = str(dur_str).lower()
                        j, m = 0, 0
                        if 'jam' in dur_str:
                            j = int(dur_str.split('jam')[0].strip())
                        elif 'j' in dur_str:
                            j = int(dur_str.split('j')[0].strip())
                        if 'menit' in dur_str:
                            m = int(dur_str.split('menit')[0].split()[-1].strip())
                        elif 'm' in dur_str:
                            b = dur_str.split('m')[0].strip()
                            m = int(b.split('j')[-1].strip()) if 'j' in b else (int(b.split('jam')[-1].strip()) if 'jam' in b else int(b))
                        return (j * 60) + m
                    except:
                        return 0

                tot = df_res['TOTAL DURASI'].apply(hitung_menit).sum()
                tj, tm = divmod(tot, 60)
                st.markdown(f'<div class="total-box"><h3>Total: {tj} Jam {tm} Menit</h3></div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {e}")

    with tab_logs:
        st.markdown("**📋 Log Aktivitas Sistem**")
        if st.button("🔄 Refresh Log"):
            st.rerun()
        try:
            data_log = sheet_log.get_all_records()
            if data_log:
                df_log = pd.DataFrame(data_log)
                cari = st.text_input("🔍 Cari...", placeholder="Filter berdasarkan kata kunci")
                if cari:
                    df_log = df_log[df_log.astype(str).apply(lambda x: x.str.contains(cari, case=False)).any(axis=1)]
                st.dataframe(df_log.iloc[::-1], use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Gagal memuat log: {e}")
