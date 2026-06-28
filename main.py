"""
app.py
-------------------------------------------------------------------
MONIVA — Monitor & Visualisasi Keuangan | Bakso Maenyos
Versi Streamlit — siap deploy di Streamlit Cloud.

Cara menjalankan lokal:
    pip install streamlit matplotlib
    streamlit run app.py

Deploy ke Streamlit Cloud:
    1. Push repo ke GitHub (minimal: app.py, database.py, requirements.txt)
    2. Buka share.streamlit.io -> New app -> pilih repo & file app.py
    3. Selesai!

Catatan: database.py TIDAK diubah sama sekali — semua logika bisnis
(CRUD, hashing, RBAC) tetap di sana persis seperti versi CustomTkinter.
-------------------------------------------------------------------
"""

import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
from datetime import date
import csv
import io
import os

# ── pastikan database tersedia & terinisialisasi ────────────────────
import database as db
db.init_db()

# =====================================================================
# PALET WARNA (cermin dari theme.py, dipakai untuk grafik matplotlib)
# =====================================================================
MERAH = "#D32F2F"
ORANYE = "#FF9800"
HIJAU = "#43A047"
BG_GELAP = "#1A1410"
BG_KARTU = "#2B2019"
TEKS_MUTED = "#A1887F"

# =====================================================================
# CSS KUSTOM — dark mode merah-oranye ala CustomTkinter
# =====================================================================
CSS = """
<style>
/* ── root & body ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #1A1410;
    color: #FFF3E0;
}
[data-testid="stSidebar"] {
    background-color: #241A14 !important;
    border-right: 1px solid #3a2a1e;
}
[data-testid="stSidebar"] * { color: #FFF3E0 !important; }

/* ── kartu / container ── */
.moniva-card {
    background: #2B2019;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    border: 1px solid #3a2a1e;
}
.moniva-badge {
    display: inline-block;
    background: #D32F2F;
    color: #FFF3E0;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 8px;
}
.moniva-badge-orange {
    background: #FF9800;
    color: #1A1410;
}
.metric-box {
    background: #2B2019;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    border: 1px solid #3a2a1e;
}
.metric-label { font-size: 12px; color: #A1887F; margin-bottom: 4px; }
.metric-value { font-size: 22px; font-weight: 700; }
.row-item {
    background: #352720;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 6px;
}

/* ── tombol ── */
.stButton > button {
    background-color: #D32F2F;
    color: #FFF3E0;
    border: none;
    border-radius: 8px;
    font-weight: 700;
    height: 40px;
}
.stButton > button:hover { background-color: #E53935; border: none; }

/* ── input ── */
.stTextInput > div > input,
.stSelectbox > div > div,
.stDateInput > div > input,
.stNumberInput > div > input {
    background-color: #352720 !important;
    color: #FFF3E0 !important;
    border: 1px solid #F57C00 !important;
    border-radius: 8px !important;
}
.stSelectbox > div > div { border: 1px solid #F57C00 !important; }

/* ── tab ── */
.stTabs [data-baseweb="tab-list"] { background: #2B2019; border-radius: 10px; }
.stTabs [data-baseweb="tab"] { color: #D7CCC8; }
.stTabs [aria-selected="true"] {
    background: #D32F2F !important;
    color: #FFF3E0 !important;
    border-radius: 8px;
}

/* ── judul & teks ── */
h1, h2, h3 { color: #FFF3E0 !important; }
.stMarkdown p { color: #D7CCC8; }
hr { border-color: #3a2a1e; }
</style>
"""


# =====================================================================
# HELPER: SESSION STATE
# =====================================================================
def _init_state():
    """Inisialisasi kunci session state yang diperlukan."""
    defaults = {
        "user": None,           # dict/sqlite3.Row user yang sedang login
        "page": "login",        # halaman aktif
        # State lupa password
        "lupa_step": 1,
        "lupa_username": "",
        "lupa_jawaban_cache": "",
        # State input barang bawaan (dynamic rows)
        "baris_barang": [{"barang": list(db.MASTER_BARANG.keys())[0], "dibawa": 0, "kembali": 0}],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _row_to_dict(row):
    """Mengubah sqlite3.Row ke dict biasa agar mudah diakses."""
    if row is None:
        return None
    return dict(zip(row.keys(), tuple(row)))


# =====================================================================
# HELPER: GRAFIK MATPLOTLIB
# =====================================================================
def _buat_grafik(omset_data, pengeluaran_data):
    semua_tanggal = sorted(set([t for t, _ in omset_data] + [t for t, _ in pengeluaran_data]))
    map_omset = dict(omset_data)
    map_pengeluaran = dict(pengeluaran_data)
    y_omset = [map_omset.get(t, 0) for t in semua_tanggal]
    y_pengeluaran = [map_pengeluaran.get(t, 0) for t in semua_tanggal]

    fig, ax = plt.subplots(figsize=(10, 3.6), dpi=100)
    fig.patch.set_facecolor(BG_KARTU)
    ax.set_facecolor(BG_KARTU)

    if not semua_tanggal:
        ax.text(0.5, 0.5, "Belum ada data transaksi",
                ha="center", va="center", color=TEKS_MUTED, fontsize=11,
                transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        ax.plot(semua_tanggal, y_omset, marker="o", color=ORANYE, linewidth=2.2, label="Pendapatan")
        ax.plot(semua_tanggal, y_pengeluaran, marker="o", color=MERAH, linewidth=2.2, label="Pengeluaran")
        ax.fill_between(semua_tanggal, y_omset, color=ORANYE, alpha=0.08)
        ax.fill_between(semua_tanggal, y_pengeluaran, color=MERAH, alpha=0.08)
        ax.legend(facecolor=BG_KARTU, edgecolor=BG_KARTU, labelcolor="#FFF3E0", fontsize=9, loc="upper left")
        ax.tick_params(axis="x", colors="#D7CCC8", labelsize=8, rotation=20)
        ax.tick_params(axis="y", colors="#D7CCC8", labelsize=8)
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rp {x:,.0f}"))

    for spine in ax.spines.values():
        spine.set_color("#352720")
    fig.tight_layout(pad=1.5)
    return fig


# =====================================================================
# HELPER: EKSPOR
# =====================================================================
def _buat_txt(rekap: dict) -> str:
    lines = [
        "==========================================",
        "   LAPORAN LABA RUGI - BAKSO MAENYOS",
        f"   Periode: {rekap['bulan']}",
        "==========================================\n",
        f"Total Pendapatan (Setoran Terverifikasi) : Rp {rekap['total_pendapatan']:,.0f}",
        f"Total Pengeluaran Operasional             : Rp {rekap['total_pengeluaran']:,.0f}",
        f"Total Gaji Harian Karyawan                : Rp {rekap['total_gaji']:,.0f}",
        "------------------------------------------",
        f"LABA / RUGI BERSIH                        : Rp {rekap['laba_bersih']:,.0f}",
        "==========================================",
        "Dihasilkan otomatis oleh aplikasi MONIVA.",
    ]
    return "\n".join(lines)


def _buat_csv_bytes(rekap: dict) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Laporan Laba Rugi - Bakso Maenyos"])
    w.writerow(["Periode", rekap["bulan"]])
    w.writerow([])
    w.writerow(["Komponen", "Nominal (Rp)"])
    w.writerow(["Total Pendapatan", f"{rekap['total_pendapatan']:.0f}"])
    w.writerow(["Total Pengeluaran", f"{rekap['total_pengeluaran']:.0f}"])
    w.writerow(["Total Gaji Karyawan", f"{rekap['total_gaji']:.0f}"])
    w.writerow(["Laba/Rugi Bersih", f"{rekap['laba_bersih']:.0f}"])
    return buf.getvalue().encode("utf-8")


# =====================================================================
# HALAMAN: LOGIN
# =====================================================================
def halaman_login():
    st.markdown(CSS, unsafe_allow_html=True)

    # Pusatkan konten
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:#D32F2F;'>🍜 MONIVA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#A1887F; margin-top:-12px;'>Monitor & Visualisasi Keuangan · Bakso Maenyos</p>", unsafe_allow_html=True)
        st.divider()

        username = st.text_input("Username", placeholder="Masukkan username", key="login_user")
        password = st.text_input("Password", placeholder="Masukkan password", type="password", key="login_pass")

        if st.button("Masuk", use_container_width=True):
            if not username or not password:
                st.error("Username dan password wajib diisi.")
            else:
                user = db.verifikasi_login(username, password)
                if user is None:
                    st.error("Username atau password salah.")
                else:
                    st.session_state.user = _row_to_dict(user)
                    st.session_state.page = "dashboard"
                    st.rerun()

        st.markdown("---")
        if st.button("🔑 Lupa Password?", use_container_width=True, type="secondary"):
            st.session_state.page = "lupa_password"
            st.session_state.lupa_step = 1
            st.session_state.lupa_username = username
            st.rerun()

        st.markdown("""
        <div style='background:#352720;border-radius:8px;padding:10px 14px;margin-top:8px;'>
        <span style='color:#A1887F;font-size:12px;'>
        Daftar username &amp; password ada di README.md<br>
        </span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
# HALAMAN: LUPA PASSWORD
# =====================================================================
def halaman_lupa_password():
    st.markdown(CSS, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#D32F2F;'>🔑 Lupa Password</h3>", unsafe_allow_html=True)

        step = st.session_state.lupa_step

        if step == 1:
            st.markdown("<p style='color:#A1887F;font-size:13px;'>Masukkan username Anda untuk melihat pertanyaan keamanan.</p>", unsafe_allow_html=True)
            uname = st.text_input("Username", value=st.session_state.lupa_username, key="lupa_uname_input")

            if st.button("Tampilkan Pertanyaan Keamanan", use_container_width=True):
                if not uname:
                    st.error("Username wajib diisi.")
                else:
                    pertanyaan = db.ambil_pertanyaan_keamanan(uname)
                    if pertanyaan is None:
                        st.error("Username tidak ditemukan.")
                    elif not pertanyaan:
                        st.warning("Akun ini belum memiliki pertanyaan keamanan. Hubungi Pemilik untuk reset manual.")
                    else:
                        st.session_state.lupa_username = uname
                        st.session_state["_lupa_pertanyaan"] = pertanyaan
                        st.session_state.lupa_step = 1.5
                        st.rerun()

        elif step == 1.5:
            pertanyaan = st.session_state.get("_lupa_pertanyaan", "")
            st.markdown(f"<div class='row-item'><b style='color:#FF9800;'>❓ {pertanyaan}</b></div>", unsafe_allow_html=True)
            jawaban = st.text_input("Jawaban Anda", key="lupa_jawaban")

            if st.button("Verifikasi Jawaban", use_container_width=True):
                if not jawaban:
                    st.error("Jawaban tidak boleh kosong.")
                elif not db.verifikasi_jawaban_keamanan(st.session_state.lupa_username, jawaban):
                    st.error("Jawaban keamanan salah. Coba lagi.")
                else:
                    st.session_state.lupa_jawaban_cache = jawaban
                    st.session_state.lupa_step = 2
                    st.rerun()

        elif step == 2:
            st.success("✅ Verifikasi berhasil! Buat password baru.")
            st.markdown(f"<p style='color:#A1887F;font-size:13px;'>Akun: <b>{st.session_state.lupa_username}</b></p>", unsafe_allow_html=True)
            pw_baru = st.text_input("Password Baru", type="password", placeholder="Minimal 6 karakter", key="lupa_pw1")
            pw_konfirmasi = st.text_input("Ulangi Password Baru", type="password", key="lupa_pw2")

            if st.button("Simpan Password Baru", use_container_width=True):
                if not pw_baru or not pw_konfirmasi:
                    st.error("Kedua field wajib diisi.")
                elif len(pw_baru) < 6:
                    st.error("Password minimal 6 karakter.")
                elif pw_baru != pw_konfirmasi:
                    st.error("Konfirmasi password tidak cocok.")
                else:
                    ok = db.reset_password_via_keamanan(
                        st.session_state.lupa_username,
                        st.session_state.lupa_jawaban_cache,
                        pw_baru
                    )
                    if ok:
                        st.success("Password berhasil diperbarui! Silakan login.")
                        st.session_state.lupa_step = 1
                        st.session_state.page = "login"
                        st.rerun()
                    else:
                        st.error("Terjadi kesalahan, silakan ulangi dari awal.")

        st.markdown("---")
        if st.button("← Kembali ke Login", use_container_width=True, type="secondary"):
            st.session_state.page = "login"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
# SIDEBAR (dipakai oleh kedua dashboard)
# =====================================================================
def _render_sidebar(user: dict):
    with st.sidebar:
        st.markdown(f"<h2 style='color:#D32F2F;'>🍜 MONIVA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#A1887F; margin-top:-12px; font-size:12px;'>Bakso Maenyos</p>", unsafe_allow_html=True)
        st.divider()

        role_warna = "#FF9800" if user["role"] == "Pemilik" else "#FF9800"
        st.markdown(f"""
        <div class='moniva-card' style='margin-bottom:12px;'>
            <b style='color:#FFF3E0;'>{user['nama']}</b><br>
            <span style='color:{role_warna}; font-size:12px;'>Role: {user['role']}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Ganti Password (in-sidebar expander) ──
        with st.expander("🔒 Ganti Password"):
            pw_lama = st.text_input("Password Lama", type="password", key="sb_pw_lama")
            pw_baru = st.text_input("Password Baru (min. 6 karakter)", type="password", key="sb_pw_baru")
            pw_conf = st.text_input("Ulangi Password Baru", type="password", key="sb_pw_conf")
            if st.button("Simpan Password Baru", key="sb_btn_pw"):
                if not pw_lama or not pw_baru or not pw_conf:
                    st.error("Semua field wajib diisi.")
                elif len(pw_baru) < 6:
                    st.error("Password baru minimal 6 karakter.")
                elif pw_baru != pw_conf:
                    st.error("Konfirmasi password tidak cocok.")
                elif pw_baru == pw_lama:
                    st.error("Password baru tidak boleh sama dengan password lama.")
                else:
                    ok = db.ubah_password(user["id_user"], pw_lama, pw_baru)
                    if ok:
                        st.success("Password berhasil diperbarui!")
                    else:
                        st.error("Password lama salah.")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Keluar / Logout", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# =====================================================================
# DASHBOARD KARYAWAN
# =====================================================================
def dashboard_karyawan():
    st.markdown(CSS, unsafe_allow_html=True)
    user = st.session_state.user
    _render_sidebar(user)

    st.markdown(f"## Halo, {user['nama']} 👋")
    st.markdown(
        "<p style='color:#A1887F;'>Halaman ini bersifat <b>lihat-saja (read-only)</b>. "
        "Data barang bawaan & gaji harian Anda diinput oleh Pemilik dan akan muncul otomatis di sini.</p>",
        unsafe_allow_html=True
    )
    st.divider()

    # ── Kartu Notifikasi Gaji Transparan ────────────────────────────
    st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
    st.markdown("<div class='moniva-badge moniva-badge-orange'>💰 Notifikasi Gaji Transparan</div>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color:#A1887F; font-size:12px;'>Gaji harian ({db.PERSENTASE_GAJI*100:.1f}% dari omset barang bawaan) "
        "muncul otomatis setiap kali Pemilik menginput data hari itu.</p>",
        unsafe_allow_html=True
    )

    daftar_gaji = [_row_to_dict(r) for r in db.ambil_gaji_by_user(user["id_user"])]
    if not daftar_gaji:
        st.info("Belum ada gaji yang tercatat. Menunggu input data dari Pemilik.")
    else:
        total_gaji = sum(g["jumlah_gaji"] for g in daftar_gaji)
        st.markdown(f"<b style='color:#43A047; font-size:16px;'>Total Gaji Terkumpul: Rp {total_gaji:,.0f}</b>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        for g in daftar_gaji[:6]:
            st.markdown(
                f"<div class='row-item'>"
                f"📅 <b style='color:#D7CCC8;'>{g['tgl_gaji']}</b> &nbsp;|&nbsp; "
                f"<b style='color:#FFF3E0;'>Rp {g['jumlah_gaji']:,.0f}</b>"
                f"</div>",
                unsafe_allow_html=True
            )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Riwayat Barang Bawaan ────────────────────────────────────────
    st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
    st.markdown("<div class='moniva-badge'>📦 Riwayat Barang Bawaan & Performa Saya</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#A1887F; font-size:12px;'>Data ini diinput oleh Pemilik. Anda hanya dapat melihat, tidak dapat mengubahnya.</p>", unsafe_allow_html=True)

    daftar_barang = [_row_to_dict(r) for r in db.ambil_barang_by_user(user["id_user"])]
    if not daftar_barang:
        st.info("Belum ada riwayat barang bawaan.")
    else:
        rows = []
        for b in daftar_barang:
            gaji_entry = b["nilai_omset"] * db.PERSENTASE_GAJI
            rows.append({
                "Tanggal": b["tgl_catat"],
                "Barang": b["nama_barang"],
                "Dibawa": b["jumlah_dibawa"],
                "Terjual": b["jumlah_terjual"],
                "Kembali": b["jumlah_kembali"],
                "Omset (Rp)": f"Rp {b['nilai_omset']:,.0f}",
                "Gaji (Rp)": f"Rp {gaji_entry:,.0f}",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
# DASHBOARD PEMILIK
# =====================================================================
def dashboard_pemilik():
    st.markdown(CSS, unsafe_allow_html=True)
    user = st.session_state.user
    _render_sidebar(user)

    st.markdown("## 🍜 Dashboard Pemilik — MONIVA")
    st.divider()

    tab_dasbor, tab_barang, tab_pengeluaran, tab_ekspor = st.tabs([
        "📊 Dasbor Finansial",
        "📦 Input Barang Bawaan",
        "💸 Input Pengeluaran",
        "📁 Ekspor Laporan",
    ])

    # ── TAB 1: DASBOR ────────────────────────────────────────────────
    with tab_dasbor:
        omset_data = db.rekap_omset_per_tanggal()
        pengeluaran_data = db.rekap_pengeluaran_per_tanggal()

        total_omset = sum(v for _, v in omset_data)
        total_pengeluaran = sum(v for _, v in pengeluaran_data)
        laba_bersih = total_omset - total_pengeluaran

        st.markdown("### Ringkasan Finansial Real-time")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-label'>Total Pendapatan</div>
                <div class='metric-value' style='color:#43A047;'>Rp {total_omset:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-label'>Total Pengeluaran</div>
                <div class='metric-value' style='color:#E53935;'>Rp {total_pengeluaran:,.0f}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            warna_laba = "#43A047" if laba_bersih >= 0 else "#E53935"
            st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-label'>Estimasi Laba Bersih</div>
                <div class='metric-value' style='color:{warna_laba};'>Rp {laba_bersih:,.0f}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
        st.markdown("#### 📈 Tren Pendapatan vs Pengeluaran")
        fig = _buat_grafik(omset_data, pengeluaran_data)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 2: INPUT BARANG BAWAAN ───────────────────────────────────
    with tab_barang:
        st.markdown("### 📦 Input Barang Bawaan Karyawan")
        st.markdown(
            f"<p style='color:#A1887F; font-size:13px;'>Hanya Pemilik yang dapat menginput data ini. "
            f"Tambahkan beberapa jenis barang sekaligus. "
            f"Gaji karyawan ({db.PERSENTASE_GAJI*100:.1f}% dari total omset) otomatis tersimpan setelah klik Simpan.</p>",
            unsafe_allow_html=True
        )

        col_form, col_riwayat = st.columns([1, 1])

        with col_form:
            st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
            st.markdown("<b style='color:#D32F2F;'>Catat Barang Bawaan Hari Ini</b>", unsafe_allow_html=True)

            # Pilih karyawan
            daftar_karyawan = [_row_to_dict(r) for r in db.ambil_daftar_karyawan()]
            map_nama_id = {f"{k['nama']} ({k['username']})": k["id_user"] for k in daftar_karyawan}
            nama_list = list(map_nama_id.keys()) or ["Belum ada akun Karyawan"]
            pilihan_karyawan = st.selectbox("Karyawan", nama_list, key="bb_karyawan")

            # Tanggal
            tgl_input = st.date_input("Tanggal Catat", value=date.today(), key="bb_tgl")

            # Dynamic rows
            st.markdown("<small style='color:#A1887F;'>Nama Barang | Dibawa | Kembali | Terjual* | Omset*</small>", unsafe_allow_html=True)

            nama_barang_list = list(db.MASTER_BARANG.keys())
            baris = st.session_state.baris_barang
            total_omset_preview = 0

            for i, b in enumerate(baris):
                cols = st.columns([3, 1, 1, 1, 2, 0.5])
                with cols[0]:
                    b["barang"] = st.selectbox("", nama_barang_list, index=nama_barang_list.index(b["barang"]) if b["barang"] in nama_barang_list else 0,
                                               key=f"bb_barang_{i}", label_visibility="collapsed")
                with cols[1]:
                    b["dibawa"] = st.number_input("", min_value=0, value=int(b["dibawa"]), key=f"bb_dibawa_{i}", label_visibility="collapsed")
                with cols[2]:
                    b["kembali"] = st.number_input("", min_value=0, value=int(b["kembali"]), key=f"bb_kembali_{i}", label_visibility="collapsed")

                terjual = max(0, b["dibawa"] - b["kembali"])
                harga = db.MASTER_BARANG.get(b["barang"], 0)
                omset_baris = terjual * harga
                total_omset_preview += omset_baris

                with cols[3]:
                    st.markdown(f"<div style='padding-top:28px; color:#FFF3E0;'>{terjual}</div>", unsafe_allow_html=True)
                with cols[4]:
                    st.markdown(f"<div style='padding-top:28px; color:#FF9800;'>Rp {omset_baris:,.0f}</div>", unsafe_allow_html=True)
                with cols[5]:
                    if len(baris) > 1:
                        if st.button("✕", key=f"bb_hapus_{i}", help="Hapus baris"):
                            st.session_state.baris_barang.pop(i)
                            st.rerun()
                    else:
                        st.markdown("<div style='padding-top:28px;'>—</div>", unsafe_allow_html=True)

            if st.button("＋ Tambah Baris Barang", key="bb_tambah"):
                st.session_state.baris_barang.append({
                    "barang": nama_barang_list[0], "dibawa": 0, "kembali": 0
                })
                st.rerun()

            # Preview total
            gaji_preview = total_omset_preview * db.PERSENTASE_GAJI
            st.markdown(f"""
            <div class='row-item'>
                <span style='color:#D7CCC8;'>Total Omset Harian:</span>
                <b style='color:#FF9800; float:right;'>Rp {total_omset_preview:,.0f}</b><br>
                <span style='color:#D7CCC8;'>Estimasi Gaji ({db.PERSENTASE_GAJI*100:.1f}%):</span>
                <b style='color:#43A047; float:right;'>Rp {gaji_preview:,.0f}</b>
            </div>
            """, unsafe_allow_html=True)

            if st.button("💾 Simpan & Hitung Gaji Otomatis", use_container_width=True, key="bb_simpan"):
                id_karyawan = map_nama_id.get(pilihan_karyawan)
                if id_karyawan is None:
                    st.error("Pilih karyawan yang valid.")
                else:
                    tgl_str = tgl_input.isoformat()
                    daftar_barang_valid = []
                    error_msg = None

                    for i, b in enumerate(st.session_state.baris_barang):
                        if b["barang"] not in db.MASTER_BARANG:
                            error_msg = f"Baris {i+1}: Pilih nama barang yang valid."
                            break
                        kembali_val = int(b["kembali"])
                        dibawa_val = int(b["dibawa"])
                        if kembali_val > dibawa_val:
                            error_msg = f"Baris {i+1}: Jumlah Kembali tidak boleh melebihi Jumlah Dibawa."
                            break
                        terjual_val = dibawa_val - kembali_val
                        harga_s = db.MASTER_BARANG[b["barang"]]
                        daftar_barang_valid.append({
                            "nama_barang": b["barang"],
                            "harga_satuan": harga_s,
                            "jumlah_dibawa": dibawa_val,
                            "jumlah_terjual": terjual_val,
                            "jumlah_kembali": kembali_val,
                            "nilai_omset": terjual_val * harga_s,
                        })

                    if error_msg:
                        st.error(error_msg)
                    elif not daftar_barang_valid:
                        st.error("Minimal harus ada 1 baris barang.")
                    else:
                        total_o, gaji_o = db.tambah_barang_bawaan_multi(
                            tgl_catat=tgl_str,
                            id_user=id_karyawan,
                            daftar_barang=daftar_barang_valid,
                            id_user_pencatat=user["id_user"],
                        )
                        st.success(
                            f"✅ {len(daftar_barang_valid)} jenis barang disimpan.\n\n"
                            f"Total Omset: Rp {total_o:,.0f} | Gaji: Rp {gaji_o:,.0f}"
                        )
                        # Reset form
                        st.session_state.baris_barang = [{"barang": nama_barang_list[0], "dibawa": 0, "kembali": 0}]
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        with col_riwayat:
            st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
            st.markdown("<b style='color:#FFF3E0;'>📜 Riwayat Barang Bawaan</b>", unsafe_allow_html=True)
            daftar_bb = [_row_to_dict(r) for r in db.ambil_semua_barang_bawaan()]
            if not daftar_bb:
                st.info("Belum ada data barang bawaan.")
            else:
                for b in daftar_bb[:15]:
                    harga_s = b.get("harga_satuan") or db.MASTER_BARANG.get(b["nama_barang"], 0)
                    st.markdown(f"""
                    <div class='row-item'>
                        <b style='color:#FFF3E0;'>{b['tgl_catat']} · {b['nama_karyawan']} · {b['nama_barang']}</b><br>
                        <span style='color:#FF9800; font-size:12px;'>
                            Dibawa {b['jumlah_dibawa']} · Terjual {b['jumlah_terjual']} · Kembali {b['jumlah_kembali']}
                            &nbsp;|&nbsp; @Rp {harga_s:,.0f} &nbsp;|&nbsp; Omset Rp {b['nilai_omset']:,.0f}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 3: INPUT PENGELUARAN ─────────────────────────────────────
    with tab_pengeluaran:
        col_pf, col_pr = st.columns([1, 1])

        with col_pf:
            st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
            st.markdown("<b style='color:#D32F2F;'>💸 Input Pengeluaran Baru</b>", unsafe_allow_html=True)

            tgl_p = st.date_input("Tanggal Pengeluaran", value=date.today(), key="p_tgl")
            kategori = st.selectbox("Kategori Biaya", ["Bahan Baku", "Energi", "Operasional"], key="p_kat")
            nama_item = st.text_input("Nama Barang / Kegiatan", placeholder="Contoh: Daging, Bensin Pegawai, Listrik", key="p_nama")
            nominal_str = st.text_input("Nominal Pengeluaran (Rp)", placeholder="Contoh: 150000", key="p_nominal")
            foto_nota = st.file_uploader("Foto Nota (opsional)", type=["jpg", "jpeg", "png"], key="p_foto")

            if st.button("Simpan Pengeluaran", use_container_width=True, key="p_simpan"):
                if not nama_item:
                    st.error("Nama barang/kegiatan wajib diisi.")
                else:
                    try:
                        nominal = float(nominal_str)
                        if nominal <= 0:
                            raise ValueError
                    except (ValueError, TypeError):
                        st.error("Nominal harus berupa angka positif.")
                    else:
                        foto_path = foto_nota.name if foto_nota else ""
                        db.tambah_pengeluaran(tgl_p.isoformat(), kategori, nama_item, nominal, foto_path, user["id_user"])
                        st.success("Data pengeluaran berhasil disimpan.")
                        st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

        with col_pr:
            st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
            st.markdown("<b style='color:#FFF3E0;'>📜 Riwayat Pengeluaran</b>", unsafe_allow_html=True)
            daftar_p = [_row_to_dict(r) for r in db.ambil_semua_pengeluaran()]
            if not daftar_p:
                st.info("Belum ada data pengeluaran.")
            else:
                for p in daftar_p[:15]:
                    nama_i = p["nama_item"] if p["nama_item"] else "(tanpa nama)"
                    nota_ket = "📎 ada nota" if p["foto_nota"] else "tanpa nota"
                    st.markdown(f"""
                    <div class='row-item'>
                        <b style='color:#FFF3E0;'>{p['tgl_pengeluaran']} · {p['kategori_biaya']} · {nama_i}</b><br>
                        <span style='color:#FF9800; font-size:12px;'>Rp {p['nominal_biaya']:,.0f} · {nota_ket}</span>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ── TAB 4: EKSPOR LAPORAN ────────────────────────────────────────
    with tab_ekspor:
        st.markdown("<div class='moniva-card'>", unsafe_allow_html=True)
        st.markdown("### 📁 Ekspor Laporan Laba Rugi Bulanan")
        st.markdown("<p style='color:#A1887F;font-size:13px;'>Pilih bulan yang ingin direkap, lalu unduh laporan.</p>", unsafe_allow_html=True)

        bulan_default = date.today().strftime("%Y-%m")
        bulan_input = st.text_input("Bulan (format YYYY-MM)", value=bulan_default, key="ekspor_bulan")

        rekap = None
        if bulan_input:
            try:
                rekap = db.rekap_laba_rugi_bulan(bulan_input)
            except Exception:
                st.error("Format bulan tidak valid. Gunakan format YYYY-MM, contoh: 2026-06")

        if rekap:
            warna_l = "#43A047" if rekap["laba_bersih"] >= 0 else "#E53935"
            st.markdown(f"""
            <div class='row-item'>
                <b style='color:#FFF3E0;'>Pratinjau Ringkasan Bulan {rekap['bulan']}</b><br><br>
                <span style='color:#D7CCC8;'>Total Pendapatan &nbsp;&nbsp;:</span>
                <b style='color:#43A047;'> Rp {rekap['total_pendapatan']:,.0f}</b><br>
                <span style='color:#D7CCC8;'>Total Pengeluaran &nbsp;:</span>
                <b style='color:#E53935;'> Rp {rekap['total_pengeluaran']:,.0f}</b><br>
                <span style='color:#D7CCC8;'>Total Gaji Karyawan:</span>
                <b style='color:#FF9800;'> Rp {rekap['total_gaji']:,.0f}</b><br>
                <span style='color:#D7CCC8;'>Laba Bersih &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:</span>
                <b style='color:{warna_l};'> Rp {rekap['laba_bersih']:,.0f}</b>
            </div>
            """, unsafe_allow_html=True)

            c_txt, c_csv = st.columns(2)
            with c_txt:
                txt_content = _buat_txt(rekap)
                st.download_button(
                    label="⬇️ Unduh sebagai .TXT",
                    data=txt_content,
                    file_name=f"Laporan_LabaRugi_BaksoMaenyos_{bulan_input}.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="dl_txt"
                )
            with c_csv:
                csv_bytes = _buat_csv_bytes(rekap)
                st.download_button(
                    label="⬇️ Unduh sebagai .CSV",
                    data=csv_bytes,
                    file_name=f"Laporan_LabaRugi_BaksoMaenyos_{bulan_input}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="dl_csv"
                )

        st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
# ROUTER UTAMA
# =====================================================================
def main():
    st.set_page_config(
        page_title="MONIVA — Bakso Maenyos",
        page_icon="🍜",
        layout="wide",
        initial_sidebar_state="expanded",
    )
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
