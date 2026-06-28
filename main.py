"""
app.py  —  MONIVA Streamlit Version
database.py tidak diubah sama sekali.
"""

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from datetime import date
import csv, io

import database as db
db.init_db()

# ── Warna ────────────────────────────────────────────────────────────
MERAH      = "#D32F2F"
ORANYE     = "#FF9800"
HIJAU      = "#43A047"
BG_UTAMA   = "#1A1410"
BG_SIDEBAR = "#241A14"
BG_KARTU   = "#2B2019"
BG_INPUT   = "#352720"
TEKS_UTAMA = "#FFF3E0"
TEKS_SEK   = "#D7CCC8"
TEKS_MUTED = "#A1887F"

# ── CSS ──────────────────────────────────────────────────────────────
CSS = """
<style>
/* Hapus padding default Streamlit */
#root > div:first-child { background: #1A1410; }
.stApp { background-color: #1A1410; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 1200px; }

/* Sembunyikan header Streamlit & toolbar */
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background-color: #241A14 !important; border-right: 1px solid #3a2a1e !important; }
[data-testid="stSidebar"] .block-container { padding-top: 1rem !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] span { color: #FFF3E0 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #FFF3E0 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: 1px solid #A1887F !important;
    color: #D7CCC8 !important;
    font-weight: 400 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #352720 !important;
}

/* ── Teks global ── */
p, span, label, div { color: #D7CCC8; }
h1, h2, h3, h4 { color: #FFF3E0 !important; }
.stMarkdown { color: #D7CCC8; }

/* ── Input fields ── */
input, textarea, [data-baseweb="input"] input {
    background-color: #352720 !important;
    color: #FFF3E0 !important;
    border: 1px solid #F57C00 !important;
    border-radius: 8px !important;
}
input::placeholder { color: #A1887F !important; }
[data-baseweb="base-input"] {
    background-color: #352720 !important;
    border: 1px solid #F57C00 !important;
    border-radius: 8px !important;
}

/* ── Selectbox / Combobox ── */
[data-baseweb="select"] > div:first-child,
[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background-color: #352720 !important;
    border: 1px solid #F57C00 !important;
    border-radius: 8px !important;
    color: #FFF3E0 !important;
}
[data-baseweb="select"] svg { fill: #FF9800 !important; }
[data-baseweb="popover"] { background: #352720 !important; border: 1px solid #F57C00 !important; }
[data-baseweb="menu"] li { background: #352720 !important; color: #FFF3E0 !important; }
[data-baseweb="menu"] li:hover { background: #4a3020 !important; }

/* ── Date input ── */
[data-testid="stDateInput"] input { background-color: #352720 !important; border: 1px solid #F57C00 !important; color: #FFF3E0 !important; border-radius: 8px !important; }
[data-testid="stDateInput"] button { background: #352720 !important; color: #FF9800 !important; border: none !important; }

/* ── Number input ── */
[data-testid="stNumberInput"] input { background-color: #352720 !important; border: 1px solid #F57C00 !important; color: #FFF3E0 !important; }
[data-testid="stNumberInput"] button { background: #352720 !important; color: #FF9800 !important; border: none !important; }

/* ── Tombol utama ── */
.stButton > button {
    background-color: #D32F2F !important;
    color: #FFF3E0 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    height: 42px !important;
    transition: background 0.2s;
}
.stButton > button:hover { background-color: #E53935 !important; }

/* ── Tab ── */
[data-baseweb="tab-list"] { background: #2B2019 !important; border-radius: 10px !important; gap: 4px; padding: 4px; }
[data-baseweb="tab"] { background: transparent !important; color: #D7CCC8 !important; border-radius: 8px !important; font-weight: 600; }
[aria-selected="true"][data-baseweb="tab"] { background: #D32F2F !important; color: #FFF3E0 !important; }
[data-baseweb="tab-panel"] { background: transparent !important; padding-top: 16px; }

/* ── Expander ── */
[data-testid="stExpander"] { background: #2B2019 !important; border: 1px solid #3a2a1e !important; border-radius: 10px !important; }
[data-testid="stExpander"] summary { color: #FFF3E0 !important; }
[data-testid="stExpander"] summary:hover { background: #352720 !important; border-radius: 8px; }
[data-testid="stExpander"] svg { fill: #FF9800 !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] { background: #352720 !important; border: 1px dashed #F57C00 !important; border-radius: 8px !important; }
[data-testid="stFileUploader"] span { color: #D7CCC8 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #3a2a1e !important; border-radius: 8px; overflow: hidden; }
[data-testid="stDataFrame"] th { background: #352720 !important; color: #FF9800 !important; font-weight: 700; }
[data-testid="stDataFrame"] td { background: #2B2019 !important; color: #D7CCC8 !important; }

/* ── Alert / info ── */
[data-testid="stAlert"] { background: #2B2019 !important; border: 1px solid #3a2a1e !important; border-radius: 8px !important; }
.stSuccess { border-left: 4px solid #43A047 !important; }
.stError { border-left: 4px solid #D32F2F !important; }
.stInfo { border-left: 4px solid #FF9800 !important; }
.stWarning { border-left: 4px solid #F57C00 !important; }

/* ── Divider ── */
hr { border-color: #3a2a1e !important; margin: 12px 0 !important; }

/* ── Download button ── */
[data-testid="stDownloadButton"] button {
    background: #F57C00 !important;
    color: #1A1410 !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
}
[data-testid="stDownloadButton"] button:hover { background: #FF9800 !important; }

/* ── Komponen kustom ── */
.moniva-card {
    background: #2B2019;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
    border: 1px solid #3a2a1e;
}
.metric-box {
    background: #2B2019;
    border-radius: 10px;
    padding: 20px 16px;
    text-align: center;
    border: 1px solid #3a2a1e;
    height: 100%;
}
.metric-label { font-size: 12px; color: #A1887F; margin-bottom: 6px; }
.metric-value { font-size: 24px; font-weight: 700; margin: 0; }
.row-item {
    background: #352720;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
    line-height: 1.6;
}
.preview-total {
    background: #352720;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 8px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.label-field {
    font-size: 13px;
    color: #D7CCC8;
    margin-bottom: 4px;
    margin-top: 12px;
    font-weight: 500;
}
.section-title {
    font-size: 16px;
    font-weight: 700;
    color: #FFF3E0;
    margin-bottom: 16px;
}
.user-card {
    background: #2B2019;
    border-radius: 10px;
    padding: 12px 16px;
    border: 1px solid #3a2a1e;
    margin-bottom: 16px;
}
</style>
"""


# ── Helpers ──────────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "user": None,
        "page": "login",
        "lupa_step": 1,
        "lupa_username": "",
        "lupa_jawaban_cache": "",
        "baris_barang": [{"barang": list(db.MASTER_BARANG.keys())[0], "dibawa": 0, "kembali": 0}],
        "bb_sukses_msg": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _row_to_dict(row):
    if row is None:
        return None
    return dict(zip(row.keys(), tuple(row)))


def _buat_grafik(omset_data, pengeluaran_data):
    semua_tgl = sorted(set([t for t, _ in omset_data] + [t for t, _ in pengeluaran_data]))
    map_o = dict(omset_data)
    map_p = dict(pengeluaran_data)
    y_o = [map_o.get(t, 0) for t in semua_tgl]
    y_p = [map_p.get(t, 0) for t in semua_tgl]

    fig, ax = plt.subplots(figsize=(10, 3.4), dpi=100)
    fig.patch.set_facecolor(BG_KARTU)
    ax.set_facecolor(BG_KARTU)

    if not semua_tgl:
        ax.text(0.5, 0.5, "Belum ada data transaksi",
                ha="center", va="center", color=TEKS_MUTED, fontsize=11,
                transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
    else:
        ax.plot(semua_tgl, y_o, marker="o", color=ORANYE, linewidth=2.2, label="Pendapatan")
        ax.plot(semua_tgl, y_p, marker="o", color=MERAH, linewidth=2.2, label="Pengeluaran")
        ax.fill_between(semua_tgl, y_o, color=ORANYE, alpha=0.10)
        ax.fill_between(semua_tgl, y_p, color=MERAH, alpha=0.10)
        ax.legend(facecolor=BG_KARTU, edgecolor=BG_KARTU, labelcolor=TEKS_UTAMA, fontsize=9, loc="upper left")
        ax.tick_params(axis="x", colors=TEKS_SEK, labelsize=8, rotation=20)
        ax.tick_params(axis="y", colors=TEKS_SEK, labelsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rp {x:,.0f}"))
    for sp in ax.spines.values():
        sp.set_color(BG_INPUT)
    fig.tight_layout(pad=1.5)
    return fig


def _buat_txt(rekap):
    return "\n".join([
        "==========================================",
        "   LAPORAN LABA RUGI - BAKSO MAENYOS",
        f"   Periode: {rekap['bulan']}",
        "==========================================\n",
        f"Total Pendapatan    : Rp {rekap['total_pendapatan']:,.0f}",
        f"Total Pengeluaran   : Rp {rekap['total_pengeluaran']:,.0f}",
        f"Total Gaji Karyawan : Rp {rekap['total_gaji']:,.0f}",
        "------------------------------------------",
        f"LABA / RUGI BERSIH  : Rp {rekap['laba_bersih']:,.0f}",
        "==========================================",
        "Dihasilkan otomatis oleh aplikasi MONIVA.",
    ])


def _buat_csv(rekap):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Laporan Laba Rugi - Bakso Maenyos"])
    w.writerow(["Periode", rekap["bulan"]])
    w.writerow([])
    w.writerow(["Komponen", "Nominal (Rp)"])
    w.writerow(["Total Pendapatan", rekap["total_pendapatan"]])
    w.writerow(["Total Pengeluaran", rekap["total_pengeluaran"]])
    w.writerow(["Total Gaji Karyawan", rekap["total_gaji"]])
    w.writerow(["Laba/Rugi Bersih", rekap["laba_bersih"]])
    return buf.getvalue().encode("utf-8")


# ── SIDEBAR ──────────────────────────────────────────────────────────
def _render_sidebar(user):
    with st.sidebar:
        st.markdown(f"<h2 style='color:#D32F2F; margin-bottom:0;'>🍜 MONIVA</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#A1887F; font-size:12px; margin-top:0;'>Bakso Maenyos</p>", unsafe_allow_html=True)
        st.divider()
        warna_role = ORANYE
        st.markdown(f"""
        <div class='user-card'>
            <p style='color:#FFF3E0; font-weight:700; margin:0 0 4px 0;'>{user['nama']}</p>
            <p style='color:{warna_role}; font-size:12px; margin:0;'>Role: {user['role']}</p>
        </div>""", unsafe_allow_html=True)

        with st.expander("🔒 Ganti Password"):
            pw_l = st.text_input("Password Lama", type="password", key="sb_pwl")
            pw_b = st.text_input("Password Baru (min. 6 karakter)", type="password", key="sb_pwb")
            pw_c = st.text_input("Ulangi Password Baru", type="password", key="sb_pwc")
            if st.button("Simpan Password Baru", key="sb_simpan_pw", use_container_width=True):
                if not pw_l or not pw_b or not pw_c:
                    st.error("Semua field wajib diisi.")
                elif len(pw_b) < 6:
                    st.error("Password baru minimal 6 karakter.")
                elif pw_b != pw_c:
                    st.error("Konfirmasi tidak cocok.")
                elif pw_b == pw_l:
                    st.error("Password baru tidak boleh sama dengan yang lama.")
                else:
                    ok = db.ubah_password(user["id_user"], pw_l, pw_b)
                    st.success("Berhasil diperbarui!") if ok else st.error("Password lama salah.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Keluar / Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ── HALAMAN LOGIN ─────────────────────────────────────────────────────
def halaman_login():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("""
        <div class='moniva-card' style='text-align:center; padding:32px 32px 24px 32px;'>
            <div style='font-size:48px;'>🍜</div>
            <h2 style='color:#D32F2F; margin:8px 0 2px 0;'>MONIVA</h2>
            <p style='color:#A1887F; font-size:12px; margin:0 0 4px 0;'>Monitor &amp; Visualisasi Keuangan</p>
            <p style='color:#FF9800; font-weight:700; font-size:14px; margin:0 0 20px 0;'>Bakso Maenyos</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
        st.markdown("<p class='label-field'>Username</p>", unsafe_allow_html=True)
        uname = st.text_input("Username", placeholder="Masukkan username", label_visibility="collapsed", key="l_uname")
        st.markdown("<p class='label-field'>Password</p>", unsafe_allow_html=True)
        pw = st.text_input("Password", placeholder="Masukkan password", type="password", label_visibility="collapsed", key="l_pw")

        if st.button("Masuk", use_container_width=True):
            if not uname or not pw:
                st.error("Username dan password wajib diisi.")
            else:
                user = db.verifikasi_login(uname, pw)
                if user is None:
                    st.error("Username atau password salah.")
                else:
                    st.session_state.user = _row_to_dict(user)
                    st.session_state.page = "dashboard"
                    st.rerun()

        st.markdown("<div style='text-align:center; margin-top:8px;'>", unsafe_allow_html=True)
        if st.button("🔑 Lupa Password?", use_container_width=True):
            st.session_state.page = "lupa_password"
            st.session_state.lupa_step = 1
            st.session_state.lupa_username = uname
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div style='background:#352720;border-radius:8px;padding:10px 14px;margin-top:12px;'>
            <p style='color:#A1887F;font-size:12px;margin:0;'>
            Lihat README.md untuk daftar lengkap.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ── HALAMAN LUPA PASSWORD ─────────────────────────────────────────────
def halaman_lupa_password():
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#D32F2F;'>🔑 Lupa Password</h3>", unsafe_allow_html=True)
        step = st.session_state.lupa_step

        if step == 1:
            st.markdown("<p style='color:#A1887F;font-size:13px;'>Masukkan username Anda untuk melihat pertanyaan keamanan.</p>", unsafe_allow_html=True)
            st.markdown("<p class='label-field'>Username</p>", unsafe_allow_html=True)
            uname = st.text_input("Username", value=st.session_state.lupa_username, label_visibility="collapsed", key="lp_uname")
            if st.button("Tampilkan Pertanyaan Keamanan", use_container_width=True):
                if not uname:
                    st.error("Username wajib diisi.")
                else:
                    pertanyaan = db.ambil_pertanyaan_keamanan(uname)
                    if pertanyaan is None:
                        st.error("Username tidak ditemukan.")
                    elif not pertanyaan:
                        st.warning("Akun ini belum punya pertanyaan keamanan.")
                    else:
                        st.session_state.lupa_username = uname
                        st.session_state["_lupa_q"] = pertanyaan
                        st.session_state.lupa_step = 1.5
                        st.rerun()

        elif step == 1.5:
            q = st.session_state.get("_lupa_q", "")
            st.markdown(f"<div class='row-item'><b style='color:#FF9800;'>❓ {q}</b></div>", unsafe_allow_html=True)
            st.markdown("<p class='label-field'>Jawaban Anda</p>", unsafe_allow_html=True)
            jwb = st.text_input("Jawaban", label_visibility="collapsed", key="lp_jwb")
            if st.button("Verifikasi Jawaban", use_container_width=True):
                if not jwb:
                    st.error("Jawaban tidak boleh kosong.")
                elif not db.verifikasi_jawaban_keamanan(st.session_state.lupa_username, jwb):
                    st.error("Jawaban keamanan salah.")
                else:
                    st.session_state.lupa_jawaban_cache = jwb
                    st.session_state.lupa_step = 2
                    st.rerun()

        elif step == 2:
            st.success("✅ Verifikasi berhasil!")
            st.markdown(f"<p style='color:#A1887F;font-size:13px;'>Buat password baru untuk: <b>{st.session_state.lupa_username}</b></p>", unsafe_allow_html=True)
            st.markdown("<p class='label-field'>Password Baru</p>", unsafe_allow_html=True)
            pw1 = st.text_input("Password Baru", type="password", placeholder="Minimal 6 karakter", label_visibility="collapsed", key="lp_pw1")
            st.markdown("<p class='label-field'>Ulangi Password Baru</p>", unsafe_allow_html=True)
            pw2 = st.text_input("Ulangi Password", type="password", label_visibility="collapsed", key="lp_pw2")
            if st.button("Simpan Password Baru", use_container_width=True):
                if not pw1 or not pw2:
                    st.error("Kedua field wajib diisi.")
                elif len(pw1) < 6:
                    st.error("Password minimal 6 karakter.")
                elif pw1 != pw2:
                    st.error("Konfirmasi tidak cocok.")
                else:
                    ok = db.reset_password_via_keamanan(st.session_state.lupa_username, st.session_state.lupa_jawaban_cache, pw1)
                    if ok:
                        st.success("Password berhasil diperbarui! Silakan login.")
                        st.session_state.lupa_step = 1
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("Terjadi kesalahan, ulangi dari awal.")

        st.divider()
        if st.button("← Kembali ke Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ── DASHBOARD KARYAWAN ────────────────────────────────────────────────
def dashboard_karyawan():
    user = st.session_state.user
    _render_sidebar(user)

    st.markdown(f"<h2 style='color:#FFF3E0; margin-bottom:4px;'>Halo, {user['nama']} 👋</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#A1887F; font-size:13px; margin-top:0;'>Halaman ini bersifat <b>read-only</b>. Data barang bawaan & gaji Anda diinput oleh Pemilik.</p>", unsafe_allow_html=True)
    st.divider()

    # ── Notifikasi Gaji ──────────────────────────────────────────────
    st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
    st.markdown(f"<p class='section-title'>💰 Notifikasi Gaji Transparan</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#A1887F; font-size:12px; margin-top:-8px;'>Gaji harian ({db.PERSENTASE_GAJI*100:.1f}% dari omset) muncul otomatis setiap kali Pemilik menginput data.</p>", unsafe_allow_html=True)

    daftar_gaji = [_row_to_dict(r) for r in db.ambil_gaji_by_user(user["id_user"])]
    if not daftar_gaji:
        st.info("Belum ada gaji tercatat. Menunggu input dari Pemilik.")
    else:
        total_gaji = sum(g["jumlah_gaji"] for g in daftar_gaji)
        st.markdown(f"<p style='color:#43A047; font-size:16px; font-weight:700; margin-bottom:12px;'>Total Gaji Terkumpul: Rp {total_gaji:,.0f}</p>", unsafe_allow_html=True)
        for g in daftar_gaji[:6]:
            st.markdown(f"""
            <div class='row-item' style='display:flex; justify-content:space-between; align-items:center;'>
                <span style='color:#D7CCC8;'>📅 {g['tgl_gaji']}</span>
                <b style='color:#FFF3E0;'>Rp {g['jumlah_gaji']:,.0f}</b>
            </div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Riwayat Barang ────────────────────────────────────────────────
    st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
    st.markdown("<p class='section-title'>📦 Riwayat Barang Bawaan & Performa</p>", unsafe_allow_html=True)
    st.markdown("<p style='color:#A1887F; font-size:12px; margin-top:-8px;'>Data diinput oleh Pemilik. Anda hanya dapat melihat.</p>", unsafe_allow_html=True)

    daftar_bb = [_row_to_dict(r) for r in db.ambil_barang_by_user(user["id_user"])]
    if not daftar_bb:
        st.info("Belum ada riwayat barang bawaan.")
    else:
        rows = []
        for b in daftar_bb:
            gaji_e = b["nilai_omset"] * db.PERSENTASE_GAJI
            rows.append({
                "Tanggal": b["tgl_catat"],
                "Barang": b["nama_barang"],
                "Dibawa": b["jumlah_dibawa"],
                "Terjual": b["jumlah_terjual"],
                "Kembali": b["jumlah_kembali"],
                "Omset (Rp)": f"Rp {b['nilai_omset']:,.0f}",
                "Gaji (Rp)": f"Rp {gaji_e:,.0f}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── DASHBOARD PEMILIK ─────────────────────────────────────────────────
def dashboard_pemilik():
    user = st.session_state.user
    _render_sidebar(user)

    st.markdown("<h2 style='color:#FFF3E0; margin-bottom:0;'>🍜 Dashboard Pemilik — MONIVA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#A1887F; font-size:12px; margin-top:2px;'>Bakso Maenyos · Akses Penuh</p>", unsafe_allow_html=True)
    st.divider()

    t1, t2, t3, t4 = st.tabs(["📊 Dasbor Finansial", "📦 Input Barang Bawaan", "💸 Input Pengeluaran", "📁 Ekspor Laporan"])

    # ── TAB 1: DASBOR ────────────────────────────────────────────────
    with t1:
        omset_data = db.rekap_omset_per_tanggal()
        pengeluaran_data = db.rekap_pengeluaran_per_tanggal()
        total_o = sum(v for _, v in omset_data)
        total_p = sum(v for _, v in pengeluaran_data)
        laba = total_o - total_p

        st.markdown("<p class='section-title'>Ringkasan Finansial Real-time</p>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            st.markdown(f"""<div class='metric-box'>
                <p class='metric-label'>Total Pendapatan</p>
                <p class='metric-value' style='color:#43A047;'>Rp {total_o:,.0f}</p>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='metric-box'>
                <p class='metric-label'>Total Pengeluaran</p>
                <p class='metric-value' style='color:#E53935;'>Rp {total_p:,.0f}</p>
            </div>""", unsafe_allow_html=True)
        with c3:
            wl = "#43A047" if laba >= 0 else "#E53935"
            st.markdown(f"""<div class='metric-box'>
                <p class='metric-label'>Estimasi Laba Bersih</p>
                <p class='metric-value' style='color:{wl};'>Rp {laba:,.0f}</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
        st.markdown("<p class='section-title'>📈 Tren Pendapatan vs Pengeluaran</p>", unsafe_allow_html=True)
        fig = _buat_grafik(omset_data, pengeluaran_data)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 2: INPUT BARANG BAWAAN ───────────────────────────────────
    with t2:
        st.markdown("<p class='section-title'>📦 Input Barang Bawaan Karyawan</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#A1887F; font-size:13px; margin-top:-8px;'>Hanya Pemilik yang dapat menginput. Gaji ({db.PERSENTASE_GAJI*100:.1f}% dari total omset) tersimpan otomatis.</p>", unsafe_allow_html=True)

        col_form, col_riwayat = st.columns([1.1, 0.9], gap="medium")

        with col_form:
            st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#D32F2F; font-weight:700; font-size:15px;'>Catat Barang Bawaan Hari Ini</p>", unsafe_allow_html=True)

            daftar_k = [_row_to_dict(r) for r in db.ambil_daftar_karyawan()]
            map_nk = {f"{k['nama']} ({k['username']})": k["id_user"] for k in daftar_k}
            nama_list_k = list(map_nk.keys()) or ["Belum ada akun Karyawan"]

            st.markdown("<p class='label-field'>Karyawan</p>", unsafe_allow_html=True)
            pilih_k = st.selectbox("Karyawan", nama_list_k, label_visibility="collapsed", key="bb_k")
            st.markdown("<p class='label-field'>Tanggal Catat</p>", unsafe_allow_html=True)
            tgl_bb = st.date_input("Tanggal", value=date.today(), label_visibility="collapsed", key="bb_tgl")

            # ── Dynamic rows ──
            nama_brg_list = list(db.MASTER_BARANG.keys())
            baris = st.session_state.baris_barang
            total_omset_prev = 0

            st.markdown("<p class='label-field'>Daftar Barang</p>", unsafe_allow_html=True)
            # Header kolom
            hc = st.columns([3, 1.2, 1.2, 1, 1.8, 0.6])
            for h, t in zip(hc, ["Nama Barang", "Dibawa", "Kembali", "Terjual*", "Omset (Rp)*", ""]):
                h.markdown(f"<small style='color:#A1887F; font-weight:600;'>{t}</small>", unsafe_allow_html=True)

            for i, b in enumerate(baris):
                rc = st.columns([3, 1.2, 1.2, 1, 1.8, 0.6])
                with rc[0]:
                    b["barang"] = st.selectbox("nb", nama_brg_list,
                        index=nama_brg_list.index(b["barang"]) if b["barang"] in nama_brg_list else 0,
                        key=f"bb_brg_{i}", label_visibility="collapsed")
                with rc[1]:
                    b["dibawa"] = st.number_input("db", min_value=0, value=int(b["dibawa"]),
                        key=f"bb_db_{i}", label_visibility="collapsed")
                with rc[2]:
                    b["kembali"] = st.number_input("kb", min_value=0, value=int(b["kembali"]),
                        key=f"bb_kb_{i}", label_visibility="collapsed")

                terjual_b = max(0, int(b["dibawa"]) - int(b["kembali"]))
                harga_b = db.MASTER_BARANG.get(b["barang"], 0)
                omset_b = terjual_b * harga_b
                total_omset_prev += omset_b

                with rc[3]:
                    st.markdown(f"<p style='padding-top:32px; color:#FFF3E0; text-align:center;'>{terjual_b}</p>", unsafe_allow_html=True)
                with rc[4]:
                    st.markdown(f"<p style='padding-top:32px; color:#FF9800;'>Rp {omset_b:,.0f}</p>", unsafe_allow_html=True)
                with rc[5]:
                    if len(baris) > 1:
                        if st.button("✕", key=f"bb_del_{i}"):
                            st.session_state.baris_barang.pop(i)
                            st.rerun()
                    else:
                        st.markdown("<p style='padding-top:32px; color:#3a2a1e;'>—</p>", unsafe_allow_html=True)

            if st.button("＋ Tambah Baris", key="bb_add"):
                st.session_state.baris_barang.append({"barang": nama_brg_list[0], "dibawa": 0, "kembali": 0})
                st.rerun()

            gaji_prev = total_omset_prev * db.PERSENTASE_GAJI
            st.markdown(f"""
            <div class='row-item' style='margin-top:12px;'>
                <div style='display:flex; justify-content:space-between;'>
                    <span style='color:#D7CCC8;'>Total Omset Harian</span>
                    <b style='color:#FF9800;'>Rp {total_omset_prev:,.0f}</b>
                </div>
                <div style='display:flex; justify-content:space-between; margin-top:4px;'>
                    <span style='color:#D7CCC8;'>Estimasi Gaji ({db.PERSENTASE_GAJI*100:.1f}%)</span>
                    <b style='color:#43A047;'>Rp {gaji_prev:,.0f}</b>
                </div>
            </div>""", unsafe_allow_html=True)

            if st.button("💾 Simpan & Hitung Gaji Otomatis", use_container_width=True, key="bb_simpan"):
                id_k = map_nk.get(pilih_k)
                if id_k is None:
                    st.error("Pilih karyawan yang valid.")
                else:
                    valid = []
                    err = None
                    for i, b in enumerate(st.session_state.baris_barang):
                        if b["barang"] not in db.MASTER_BARANG:
                            err = f"Baris {i+1}: pilih barang yang valid."
                            break
                        dw, kw = int(b["dibawa"]), int(b["kembali"])
                        if kw > dw:
                            err = f"Baris {i+1}: Kembali tidak boleh > Dibawa."
                            break
                        tj = dw - kw
                        hs = db.MASTER_BARANG[b["barang"]]
                        valid.append({"nama_barang": b["barang"], "harga_satuan": hs,
                                      "jumlah_dibawa": dw, "jumlah_terjual": tj,
                                      "jumlah_kembali": kw, "nilai_omset": tj * hs})
                    if err:
                        st.error(err)
                    else:
                        to, go = db.tambah_barang_bawaan_multi(
                            tgl_catat=tgl_bb.isoformat(), id_user=id_k,
                            daftar_barang=valid, id_user_pencatat=user["id_user"])
                        st.success(f"✅ {len(valid)} barang disimpan · Omset: Rp {to:,.0f} · Gaji: Rp {go:,.0f}")
                        st.session_state.baris_barang = [{"barang": nama_brg_list[0], "dibawa": 0, "kembali": 0}]
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        with col_riwayat:
            st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
            st.markdown("<p class='section-title'>📜 Riwayat Barang Bawaan</p>", unsafe_allow_html=True)
            daftar_bb = [_row_to_dict(r) for r in db.ambil_semua_barang_bawaan()]
            if not daftar_bb:
                st.info("Belum ada data barang bawaan.")
            else:
                for b in daftar_bb[:15]:
                    hs = b.get("harga_satuan") or db.MASTER_BARANG.get(b["nama_barang"], 0)
                    st.markdown(f"""
                    <div class='row-item'>
                        <b style='color:#FFF3E0;'>{b['tgl_catat']} · {b['nama_karyawan']}</b><br>
                        <span style='color:#FF9800;'>{b['nama_barang']}</span>
                        <span style='color:#A1887F; font-size:12px;'> · Dibawa {b['jumlah_dibawa']} · Terjual {b['jumlah_terjual']} · Kembali {b['jumlah_kembali']}</span><br>
                        <span style='color:#D7CCC8; font-size:12px;'>@Rp {hs:,.0f} · Omset <b style='color:#FFF3E0;'>Rp {b['nilai_omset']:,.0f}</b></span>
                    </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 3: INPUT PENGELUARAN ─────────────────────────────────────
    with t3:
        st.markdown("<p class='section-title'>💸 Input Pengeluaran</p>", unsafe_allow_html=True)
        col_pf, col_pr = st.columns([1.1, 0.9], gap="medium")

        with col_pf:
            st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
            st.markdown("<p style='color:#D32F2F; font-weight:700; font-size:15px;'>Input Pengeluaran Baru</p>", unsafe_allow_html=True)

            st.markdown("<p class='label-field'>Tanggal Pengeluaran</p>", unsafe_allow_html=True)
            tgl_p = st.date_input("TglP", value=date.today(), label_visibility="collapsed", key="p_tgl")
            st.markdown("<p class='label-field'>Kategori Biaya</p>", unsafe_allow_html=True)
            kat = st.selectbox("KatP", ["Bahan Baku", "Energi", "Operasional"], label_visibility="collapsed", key="p_kat")
            st.markdown("<p class='label-field'>Nama Barang / Kegiatan</p>", unsafe_allow_html=True)
            nama_p = st.text_input("NamaP", placeholder="Contoh: Daging, Bensin Pegawai, Listrik", label_visibility="collapsed", key="p_nama")
            st.markdown("<p class='label-field'>Nominal Pengeluaran (Rp)</p>", unsafe_allow_html=True)
            nominal_p = st.text_input("NomP", placeholder="Contoh: 150000", label_visibility="collapsed", key="p_nom")
            st.markdown("<p class='label-field'>Foto Nota (opsional)</p>", unsafe_allow_html=True)
            foto = st.file_uploader("FotoP", type=["jpg","jpeg","png"], label_visibility="collapsed", key="p_foto")

            if st.button("Simpan Pengeluaran", use_container_width=True, key="p_simpan"):
                if not nama_p:
                    st.error("Nama barang/kegiatan wajib diisi.")
                else:
                    try:
                        nom = float(nominal_p)
                        if nom <= 0: raise ValueError
                    except (ValueError, TypeError):
                        st.error("Nominal harus berupa angka positif.")
                    else:
                        db.tambah_pengeluaran(tgl_p.isoformat(), kat, nama_p, nom,
                                              foto.name if foto else "", user["id_user"])
                        st.success("Data pengeluaran berhasil disimpan.")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_pr:
            st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
            st.markdown("<p class='section-title'>📜 Riwayat Pengeluaran</p>", unsafe_allow_html=True)
            daftar_p = [_row_to_dict(r) for r in db.ambil_semua_pengeluaran()]
            if not daftar_p:
                st.info("Belum ada data pengeluaran.")
            else:
                for p in daftar_p[:15]:
                    ni = p["nama_item"] if p["nama_item"] else "(tanpa nama)"
                    nt = "📎 ada nota" if p["foto_nota"] else "tanpa nota"
                    st.markdown(f"""
                    <div class='row-item'>
                        <b style='color:#FFF3E0;'>{p['tgl_pengeluaran']} · {p['kategori_biaya']}</b><br>
                        <span style='color:#D7CCC8;'>{ni}</span><br>
                        <span style='color:#FF9800; font-weight:700;'>Rp {p['nominal_biaya']:,.0f}</span>
                        <span style='color:#A1887F; font-size:12px;'> · {nt}</span>
                    </div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 4: EKSPOR LAPORAN ────────────────────────────────────────
    with t4:
        st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
        st.markdown("<p class='section-title'>📁 Ekspor Laporan Laba Rugi Bulanan</p>", unsafe_allow_html=True)
        st.markdown("<p style='color:#A1887F; font-size:13px;'>Pilih bulan yang ingin direkap, lalu unduh laporan dalam format TXT atau CSV.</p>", unsafe_allow_html=True)

        st.markdown("<p class='label-field'>Bulan (format YYYY-MM)</p>", unsafe_allow_html=True)
        bulan_in = st.text_input("Bulan", value=date.today().strftime("%Y-%m"), label_visibility="collapsed", key="eksp_bln")

        rekap = None
        if bulan_in:
            try:
                rekap = db.rekap_laba_rugi_bulan(bulan_in)
            except Exception:
                st.error("Format bulan tidak valid. Gunakan YYYY-MM, contoh: 2026-06")

        if rekap:
            wl2 = "#43A047" if rekap["laba_bersih"] >= 0 else "#E53935"
            st.markdown(f"""
            <div class='row-item' style='margin: 12px 0;'>
                <p style='color:#FFF3E0; font-weight:700; margin:0 0 10px 0;'>Pratinjau — Bulan {rekap['bulan']}</p>
                <div style='display:flex; justify-content:space-between; margin-bottom:4px;'>
                    <span style='color:#D7CCC8;'>Total Pendapatan</span>
                    <b style='color:#43A047;'>Rp {rekap['total_pendapatan']:,.0f}</b>
                </div>
                <div style='display:flex; justify-content:space-between; margin-bottom:4px;'>
                    <span style='color:#D7CCC8;'>Total Pengeluaran</span>
                    <b style='color:#E53935;'>Rp {rekap['total_pengeluaran']:,.0f}</b>
                </div>
                <div style='display:flex; justify-content:space-between; margin-bottom:4px;'>
                    <span style='color:#D7CCC8;'>Total Gaji Karyawan</span>
                    <b style='color:#FF9800;'>Rp {rekap['total_gaji']:,.0f}</b>
                </div>
                <hr style='margin:8px 0;'>
                <div style='display:flex; justify-content:space-between;'>
                    <span style='color:#D7CCC8; font-weight:700;'>Laba / Rugi Bersih</span>
                    <b style='color:{wl2}; font-size:16px;'>Rp {rekap['laba_bersih']:,.0f}</b>
                </div>
            </div>""", unsafe_allow_html=True)

            dc, cc = st.columns(2, gap="medium")
            with dc:
                st.download_button("⬇️ Unduh .TXT", _buat_txt(rekap),
                    file_name=f"LabaRugi_BaksoMaenyos_{bulan_in}.txt",
                    mime="text/plain", use_container_width=True)
            with cc:
                st.download_button("⬇️ Unduh .CSV", _buat_csv(rekap),
                    file_name=f"LabaRugi_BaksoMaenyos_{bulan_in}.csv",
                    mime="text/csv", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)


# ── MAIN ──────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="MONIVA — Bakso Maenyos",
        page_icon="🍜",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)
    _init_state()

    page = st.session_state.page
    user = st.session_state.user

    if page == "login" or user is None:
        halaman_login()
    elif page == "lupa_password":
        halaman_lupa_password()
    elif page == "dashboard":
        if user["role"] == "Pemilik":
            dashboard_pemilik()
        else:
            dashboard_karyawan()


if __name__ == "__main__":
    main()
