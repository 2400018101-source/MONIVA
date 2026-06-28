"""
database.py
-------------------------------------------------------------------
Modul khusus untuk mengelola seluruh interaksi dengan database
SQLite milik aplikasi MONIVA (Monitor and Visualisasi).

Berisi:
- Pembuatan tabel otomatis saat aplikasi pertama kali dijalankan
- Data dummy awal: 1 akun Pemilik (placeholder, WAJIB diganti) & 5 akun
  Karyawan unik, agar bisa langsung diuji
- Fungsi-fungsi CRUD yang dipanggil oleh halaman-halaman GUI

Catatan keamanan:
Untuk kebutuhan demo/UMKM skala kecil, password disimpan dengan hashing
SHA-256 sederhana (bukan plaintext) supaya tetap mudah diverifikasi
tanpa dependency tambahan seperti bcrypt.
-------------------------------------------------------------------
"""

import sqlite3
import hashlib
import os
from datetime import date

# Lokasi file database disimpan sejajar dengan skrip aplikasi
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moniva.db")

# Persentase gaji harian karyawan dari total omset/setoran (17.5%)
PERSENTASE_GAJI = 0.175

# =====================================================================
# MASTER DAFTAR BARANG & HARGA SATUAN
# Dipakai untuk dropdown pilihan barang dan kalkulasi omset otomatis.
# Format: {nama_barang: harga_satuan}
# =====================================================================
MASTER_BARANG = {
    "Mie": 2000,
    "Pangsit Mekar": 2000,
    "Tahu": 2000,
    "Siomay": 2000,
    "Bakso Halus": 1500,
    "Bakso Urat": 3000,
    "Bakso Cincang": 6000,
}


def hash_password(password: str) -> str:
    """Mengubah password teks biasa menjadi hash SHA-256 (hex string)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_connection():
    """
    Membuka koneksi baru ke database SQLite.
    Setiap fungsi membuka koneksi sendiri agar aman dipakai dari
    beberapa bagian GUI tanpa konflik thread/cursor.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # agar hasil query bisa diakses seperti dict
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Membuat semua tabel yang dibutuhkan MONIVA jika belum ada,
    lalu mengisi data dummy awal (hanya sekali, saat tabel masih kosong).
    Fungsi ini WAJIB dipanggil sekali di awal program (main.py).
    """
    conn = get_connection()
    cur = conn.cursor()

    # --- tb_user: data login & peran pengguna ---------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tb_user (
            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nama TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Karyawan', 'Pemilik')),
            pertanyaan_keamanan TEXT,
            jawaban_keamanan TEXT
        )
    """)

    # --- tb_setoran_harian (dipertahankan untuk kompatibilitas historis) ---
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tb_setoran_harian (
            id_setoran INTEGER PRIMARY KEY AUTOINCREMENT,
            tgl_setoran TEXT NOT NULL,
            nominal_setoran REAL NOT NULL,
            status_setoran TEXT NOT NULL DEFAULT 'Pending'
                CHECK(status_setoran IN ('Pending', 'Verified')),
            id_user INTEGER NOT NULL,
            FOREIGN KEY (id_user) REFERENCES tb_user(id_user)
        )
    """)

    # --- tb_barang_bawaan: catatan barang/stok yang dibawa karyawan ------
    # REVISI: setiap baris mewakili SATU jenis barang untuk satu karyawan
    # pada satu tanggal. Satu hari bisa terdiri dari banyak baris (multi-barang).
    # id_sesi_input dipakai untuk mengelompokkan baris-baris yang diinput
    # dalam 1 kali proses simpan (satu "sesi"), agar gaji harian dapat
    # dihitung dari TOTAL omset seluruh barang dalam sesi tersebut.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tb_barang_bawaan (
            id_barang INTEGER PRIMARY KEY AUTOINCREMENT,
            tgl_catat TEXT NOT NULL,
            id_user INTEGER NOT NULL,
            nama_barang TEXT NOT NULL,
            harga_satuan REAL NOT NULL DEFAULT 0,
            jumlah_dibawa INTEGER NOT NULL,
            jumlah_terjual INTEGER NOT NULL,
            jumlah_kembali INTEGER NOT NULL,
            nilai_omset REAL NOT NULL,
            id_user_pencatat INTEGER NOT NULL,
            id_sesi_input INTEGER,
            FOREIGN KEY (id_user) REFERENCES tb_user(id_user),
            FOREIGN KEY (id_user_pencatat) REFERENCES tb_user(id_user)
        )
    """)

    # --- tb_gaji_harian: gaji yang otomatis terhitung --------------------
    # REVISI: id_sesi_input ditambahkan agar satu entri gaji merujuk ke
    # satu sesi input multi-barang, bukan hanya satu baris barang.
    # id_barang tetap dipertahankan untuk kompatibilitas data lama.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tb_gaji_harian (
            id_gaji INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER NOT NULL,
            id_setoran INTEGER,
            id_barang INTEGER,
            id_sesi_input INTEGER,
            tgl_gaji TEXT NOT NULL,
            total_omset REAL NOT NULL,
            jumlah_gaji REAL NOT NULL,
            FOREIGN KEY (id_user) REFERENCES tb_user(id_user),
            FOREIGN KEY (id_setoran) REFERENCES tb_setoran_harian(id_setoran),
            FOREIGN KEY (id_barang) REFERENCES tb_barang_bawaan(id_barang)
        )
    """)

    # --- tb_pengeluaran: biaya operasional toko --------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tb_pengeluaran (
            id_pengeluaran INTEGER PRIMARY KEY AUTOINCREMENT,
            tgl_pengeluaran TEXT NOT NULL,
            kategori_biaya TEXT NOT NULL,
            nama_item TEXT NOT NULL DEFAULT '',
            nominal_biaya REAL NOT NULL,
            foto_nota TEXT,
            id_user INTEGER NOT NULL,
            FOREIGN KEY (id_user) REFERENCES tb_user(id_user)
        )
    """)

    conn.commit()

    # Migrasi: tambah kolom baru jika belum ada (untuk database lama)
    for kolom, tipe_default in [
        ("harga_satuan", "REAL NOT NULL DEFAULT 0"),
        ("id_sesi_input", "INTEGER"),
    ]:
        try:
            cur.execute(f"ALTER TABLE tb_barang_bawaan ADD COLUMN {kolom} {tipe_default}")
            conn.commit()
        except Exception:
            pass  # kolom sudah ada, abaikan

    try:
        cur.execute("ALTER TABLE tb_gaji_harian ADD COLUMN id_sesi_input INTEGER")
        conn.commit()
    except Exception:
        pass

    try:
        cur.execute("ALTER TABLE tb_pengeluaran ADD COLUMN nama_item TEXT NOT NULL DEFAULT ''")
        conn.commit()
    except Exception:
        pass

    # --- Seed data dummy hanya jika tabel user masih kosong --------------
    cur.execute("SELECT COUNT(*) AS total FROM tb_user")
    total_user = cur.fetchone()["total"]

    if total_user == 0:
        pertanyaan_default = "Apa nama hewan peliharaan favorit Anda?"

        cur.executemany(
            """INSERT INTO tb_user
               (username, password, nama, role, pertanyaan_keamanan, jawaban_keamanan)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                ("davahaidar", hash_password("1933"),
                 "Dava (Pemilik)", "Pemilik",
                 pertanyaan_default, hash_password("kucing")),
                ("budi_karyawan", hash_password("budi123"), "Budi Santoso", "Karyawan",
                 pertanyaan_default, hash_password("rocky")),
                ("siti_karyawan", hash_password("siti123"), "Siti Aminah", "Karyawan",
                 pertanyaan_default, hash_password("milo")),
                ("joko_karyawan", hash_password("joko123"), "Joko Prasetyo", "Karyawan",
                 pertanyaan_default, hash_password("bobby")),
                ("rina_karyawan", hash_password("rina123"), "Rina Wulandari", "Karyawan",
                 pertanyaan_default, hash_password("luna")),
                ("agus_karyawan", hash_password("agus123"), "Agus Setiawan", "Karyawan",
                 pertanyaan_default, hash_password("max")),
            ]
        )
        conn.commit()

        id_karyawan = cur.execute(
            "SELECT id_user FROM tb_user WHERE username = 'budi_karyawan'"
        ).fetchone()["id_user"]
        id_pemilik = cur.execute(
            "SELECT id_user FROM tb_user WHERE username = 'GANTI_USERNAME_ADMIN'"
        ).fetchone()["id_user"]

        cur.execute(
            """INSERT INTO tb_setoran_harian
               (tgl_setoran, nominal_setoran, status_setoran, id_user)
               VALUES (?, ?, ?, ?)""",
            ("2026-06-10", 850000, "Verified", id_karyawan)
        )

        daftar_karyawan = cur.execute(
            "SELECT id_user, nama FROM tb_user WHERE role = 'Karyawan' ORDER BY id_user"
        ).fetchall()

        # Contoh data multi-barang untuk 3 hari (simulasi sesi input baru)
        contoh_sesi = [
            # (tgl, id_karyawan_idx, list_of_(nama_barang, dibawa, kembali))
            ("2026-06-18", 0, [("Bakso Urat", 50, 5), ("Bakso Halus", 60, 8)]),
            ("2026-06-19", 1, [("Mie", 80, 10), ("Siomay", 40, 4)]),
            ("2026-06-20", 2, [("Bakso Cincang", 30, 2), ("Tahu", 50, 5)]),
        ]

        for tgl, idx, barang_list in contoh_sesi:
            uid = daftar_karyawan[idx % len(daftar_karyawan)]["id_user"]
            total_omset_sesi = 0
            id_barang_pertama = None

            for nama_barang, dibawa, kembali in barang_list:
                harga = MASTER_BARANG.get(nama_barang, 0)
                terjual = dibawa - kembali
                omset = terjual * harga
                total_omset_sesi += omset

                cur.execute(
                    """INSERT INTO tb_barang_bawaan
                       (tgl_catat, id_user, nama_barang, harga_satuan, jumlah_dibawa,
                        jumlah_terjual, jumlah_kembali, nilai_omset, id_user_pencatat)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (tgl, uid, nama_barang, harga, dibawa, terjual, kembali, omset, id_pemilik)
                )
                if id_barang_pertama is None:
                    id_barang_pertama = cur.lastrowid

            # Satu entri gaji per sesi (total seluruh barang)
            gaji = total_omset_sesi * PERSENTASE_GAJI
            cur.execute(
                """INSERT INTO tb_gaji_harian
                   (id_user, id_barang, tgl_gaji, total_omset, jumlah_gaji)
                   VALUES (?, ?, ?, ?, ?)""",
                (uid, id_barang_pertama, tgl, total_omset_sesi, gaji)
            )

        contoh_pengeluaran = [
            ("2026-06-18", "Bahan Baku", 350000, "", id_pemilik),
            ("2026-06-19", "Energi", 75000, "", id_pemilik),
            ("2026-06-20", "Operasional", 120000, "", id_pemilik),
        ]
        cur.executemany(
            """INSERT INTO tb_pengeluaran
               (tgl_pengeluaran, kategori_biaya, nominal_biaya, foto_nota, id_user)
               VALUES (?, ?, ?, ?, ?)""",
            contoh_pengeluaran
        )
        conn.commit()

    conn.close()


# =====================================================================
# FUNGSI AUTENTIKASI
# =====================================================================

def verifikasi_login(username: str, password: str):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM tb_user WHERE username = ? AND password = ?",
        (username, hash_password(password))
    ).fetchone()
    conn.close()
    return user


def cek_username_ada(username: str):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM tb_user WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return user


def ambil_pertanyaan_keamanan(username: str):
    conn = get_connection()
    user = conn.execute(
        "SELECT pertanyaan_keamanan FROM tb_user WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if user is None:
        return None
    return user["pertanyaan_keamanan"]


def verifikasi_jawaban_keamanan(username: str, jawaban: str) -> bool:
    conn = get_connection()
    user = conn.execute(
        "SELECT jawaban_keamanan FROM tb_user WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if user is None or not user["jawaban_keamanan"]:
        return False
    return user["jawaban_keamanan"] == hash_password(jawaban.strip().lower())


def reset_password_via_keamanan(username: str, jawaban: str, password_baru: str) -> bool:
    if not verifikasi_jawaban_keamanan(username, jawaban):
        return False
    conn = get_connection()
    conn.execute(
        "UPDATE tb_user SET password = ? WHERE username = ?",
        (hash_password(password_baru), username)
    )
    conn.commit()
    conn.close()
    return True


def ubah_password(id_user: int, password_lama: str, password_baru: str) -> bool:
    conn = get_connection()
    user = conn.execute(
        "SELECT password FROM tb_user WHERE id_user = ?", (id_user,)
    ).fetchone()

    if user is None or user["password"] != hash_password(password_lama):
        conn.close()
        return False

    conn.execute(
        "UPDATE tb_user SET password = ? WHERE id_user = ?",
        (hash_password(password_baru), id_user)
    )
    conn.commit()
    conn.close()
    return True


def ubah_jawaban_keamanan(id_user: int, pertanyaan: str, jawaban: str):
    conn = get_connection()
    conn.execute(
        "UPDATE tb_user SET pertanyaan_keamanan = ?, jawaban_keamanan = ? WHERE id_user = ?",
        (pertanyaan, hash_password(jawaban.strip().lower()), id_user)
    )
    conn.commit()
    conn.close()


# =====================================================================
# FUNGSI SETORAN HARIAN (ALUR LAMA — dipertahankan untuk kompatibilitas)
# =====================================================================

def tambah_setoran(tgl_setoran: str, nominal_setoran: float, id_user: int):
    """[DEPRECATED] Menambahkan setoran baru dengan status default 'Pending'."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO tb_setoran_harian (tgl_setoran, nominal_setoran, status_setoran, id_user)
           VALUES (?, ?, 'Pending', ?)""",
        (tgl_setoran, nominal_setoran, id_user)
    )
    conn.commit()
    conn.close()


def ambil_setoran_by_user(id_user: int):
    """[DEPRECATED] Mengambil seluruh riwayat setoran milik satu karyawan."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM tb_setoran_harian
           WHERE id_user = ?
           ORDER BY tgl_setoran DESC, id_setoran DESC""",
        (id_user,)
    ).fetchall()
    conn.close()
    return rows


def ambil_setoran_pending():
    """[DEPRECATED] Mengambil semua setoran berstatus Pending."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, u.nama AS nama_karyawan
           FROM tb_setoran_harian s
           JOIN tb_user u ON s.id_user = u.id_user
           WHERE s.status_setoran = 'Pending'
           ORDER BY s.tgl_setoran ASC"""
    ).fetchall()
    conn.close()
    return rows


def ambil_semua_setoran():
    """[DEPRECATED] Mengambil seluruh data setoran (riwayat lama)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT s.*, u.nama AS nama_karyawan
           FROM tb_setoran_harian s
           JOIN tb_user u ON s.id_user = u.id_user
           ORDER BY s.tgl_setoran DESC, s.id_setoran DESC"""
    ).fetchall()
    conn.close()
    return rows


def approve_setoran(id_setoran: int):
    """[DEPRECATED] Menyetujui setoran & menghitung gaji otomatis."""
    conn = get_connection()
    setoran = conn.execute(
        "SELECT * FROM tb_setoran_harian WHERE id_setoran = ?",
        (id_setoran,)
    ).fetchone()

    if setoran is None:
        conn.close()
        raise ValueError("Setoran tidak ditemukan.")

    if setoran["status_setoran"] == "Verified":
        conn.close()
        raise ValueError("Setoran ini sudah diverifikasi sebelumnya.")

    conn.execute(
        "UPDATE tb_setoran_harian SET status_setoran = 'Verified' WHERE id_setoran = ?",
        (id_setoran,)
    )

    total_omset = setoran["nominal_setoran"]
    jumlah_gaji = total_omset * PERSENTASE_GAJI

    conn.execute(
        """INSERT INTO tb_gaji_harian (id_user, id_setoran, tgl_gaji, total_omset, jumlah_gaji)
           VALUES (?, ?, ?, ?, ?)""",
        (setoran["id_user"], id_setoran, setoran["tgl_setoran"], total_omset, jumlah_gaji)
    )

    conn.commit()
    conn.close()
    return jumlah_gaji


# =====================================================================
# FUNGSI BARANG BAWAAN (ALUR BARU — MULTI-BARANG PER SESI)
# RBAC: hanya Pemilik yang boleh menginput/mengubah.
# =====================================================================

def tambah_barang_bawaan_multi(tgl_catat: str, id_user: int,
                                daftar_barang: list, id_user_pencatat: int) -> float:
    """
    Mencatat BEBERAPA jenis barang sekaligus untuk satu karyawan dalam satu hari
    (multi-barang per sesi), lalu LANGSUNG menghitung & menyimpan gaji harian.

    Parameter:
        tgl_catat        -> tanggal pencatatan (YYYY-MM-DD)
        id_user          -> id karyawan yang membawa barang
        daftar_barang    -> list of dict, tiap dict berisi:
                           {nama_barang, harga_satuan, jumlah_dibawa,
                            jumlah_terjual, jumlah_kembali, nilai_omset}
        id_user_pencatat -> id Pemilik yang menginput (audit trail)

    Mengembalikan tuple (total_omset, jumlah_gaji) dari sesi input ini.
    """
    conn = get_connection()
    total_omset_sesi = 0.0
    id_barang_pertama = None

    for barang in daftar_barang:
        conn.execute(
            """INSERT INTO tb_barang_bawaan
               (tgl_catat, id_user, nama_barang, harga_satuan, jumlah_dibawa,
                jumlah_terjual, jumlah_kembali, nilai_omset, id_user_pencatat)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tgl_catat, id_user,
                barang["nama_barang"], barang["harga_satuan"],
                barang["jumlah_dibawa"], barang["jumlah_terjual"],
                barang["jumlah_kembali"], barang["nilai_omset"],
                id_user_pencatat,
            )
        )
        id_baru = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
        if id_barang_pertama is None:
            id_barang_pertama = id_baru
        total_omset_sesi += barang["nilai_omset"]

    # Satu entri gaji per sesi (total SEMUA barang pada hari itu)
    jumlah_gaji = total_omset_sesi * PERSENTASE_GAJI
    conn.execute(
        """INSERT INTO tb_gaji_harian
           (id_user, id_barang, tgl_gaji, total_omset, jumlah_gaji)
           VALUES (?, ?, ?, ?, ?)""",
        (id_user, id_barang_pertama, tgl_catat, total_omset_sesi, jumlah_gaji)
    )

    conn.commit()
    conn.close()
    return total_omset_sesi, jumlah_gaji


def tambah_barang_bawaan(tgl_catat: str, id_user: int, nama_barang: str,
                          jumlah_dibawa: int, jumlah_terjual: int, jumlah_kembali: int,
                          nilai_omset: float, id_user_pencatat: int) -> float:
    """
    [COMPAT] Wrapper satu-barang untuk kompatibilitas kode lama.
    Memanggil tambah_barang_bawaan_multi dengan satu item.
    """
    harga_satuan = MASTER_BARANG.get(nama_barang, 0)
    daftar = [{
        "nama_barang": nama_barang,
        "harga_satuan": harga_satuan,
        "jumlah_dibawa": jumlah_dibawa,
        "jumlah_terjual": jumlah_terjual,
        "jumlah_kembali": jumlah_kembali,
        "nilai_omset": nilai_omset,
    }]
    _, jumlah_gaji = tambah_barang_bawaan_multi(tgl_catat, id_user, daftar, id_user_pencatat)
    return jumlah_gaji


def ambil_barang_by_user(id_user: int):
    """
    [READ-ONLY] Mengambil seluruh riwayat barang bawaan milik satu karyawan.
    Dipakai oleh Dashboard Karyawan — karyawan hanya bisa MELIHAT.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM tb_barang_bawaan
           WHERE id_user = ?
           ORDER BY tgl_catat DESC, id_barang DESC""",
        (id_user,)
    ).fetchall()
    conn.close()
    return rows


def ambil_semua_barang_bawaan():
    """
    Mengambil seluruh data barang bawaan dari semua karyawan, beserta nama
    karyawan & nama pencatatnya. Dipakai oleh Dashboard Pemilik.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT b.*, u.nama AS nama_karyawan, p.nama AS nama_pencatat
           FROM tb_barang_bawaan b
           JOIN tb_user u ON b.id_user = u.id_user
           JOIN tb_user p ON b.id_user_pencatat = p.id_user
           ORDER BY b.tgl_catat DESC, b.id_barang DESC"""
    ).fetchall()
    conn.close()
    return rows


def ambil_daftar_karyawan():
    """Mengambil daftar ringkas semua akun ber-role Karyawan, untuk dropdown form."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id_user, nama, username FROM tb_user WHERE role = 'Karyawan' ORDER BY nama ASC"
    ).fetchall()
    conn.close()
    return rows


# =====================================================================
# FUNGSI GAJI HARIAN
# =====================================================================

def ambil_gaji_by_user(id_user: int):
    """
    [READ-ONLY] Mengambil riwayat gaji harian milik seorang karyawan.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM tb_gaji_harian
           WHERE id_user = ?
           ORDER BY tgl_gaji DESC, id_gaji DESC""",
        (id_user,)
    ).fetchall()
    conn.close()
    return rows


# =====================================================================
# FUNGSI PENGELUARAN
# =====================================================================

def tambah_pengeluaran(tgl_pengeluaran: str, kategori_biaya: str, nama_item: str,
                        nominal_biaya: float, foto_nota: str, id_user: int):
    """Menambahkan data pengeluaran baru (biaya operasional toko).

    nama_item adalah nama barang/kegiatan yang diisi manual oleh Pemilik,
    contoh: "Daging" (kategori Bahan Baku) atau "Bensin Pegawai"
    (kategori Operasional). Kategori tetap berupa pilihan dropdown,
    sementara nama_item bebas diketik agar lebih spesifik & mudah dilacak.
    """
    conn = get_connection()
    conn.execute(
        """INSERT INTO tb_pengeluaran
           (tgl_pengeluaran, kategori_biaya, nama_item, nominal_biaya, foto_nota, id_user)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (tgl_pengeluaran, kategori_biaya, nama_item, nominal_biaya, foto_nota, id_user)
    )
    conn.commit()
    conn.close()


def ambil_semua_pengeluaran():
    """Mengambil seluruh data pengeluaran, terbaru di atas."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tb_pengeluaran ORDER BY tgl_pengeluaran DESC, id_pengeluaran DESC"
    ).fetchall()
    conn.close()
    return rows


# =====================================================================
# FUNGSI REKAP / LAPORAN (untuk grafik & ekspor)
# =====================================================================

def rekap_omset_per_tanggal():
    """
    Mengembalikan list (tanggal, total_omset) untuk grafik Pendapatan.
    Bersumber dari nilai_omset di tb_barang_bawaan.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT tgl_catat AS tanggal, SUM(nilai_omset) AS total
           FROM tb_barang_bawaan
           GROUP BY tgl_catat
           ORDER BY tgl_catat ASC"""
    ).fetchall()
    conn.close()
    return [(r["tanggal"], r["total"]) for r in rows]


def rekap_pengeluaran_per_tanggal():
    """Mengembalikan list (tanggal, total_pengeluaran) untuk grafik Pengeluaran."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT tgl_pengeluaran AS tanggal, SUM(nominal_biaya) AS total
           FROM tb_pengeluaran
           GROUP BY tgl_pengeluaran
           ORDER BY tgl_pengeluaran ASC"""
    ).fetchall()
    conn.close()
    return [(r["tanggal"], r["total"]) for r in rows]


def rekap_laba_rugi_bulan(bulan: str):
    """
    Menghitung ringkasan Laba Rugi untuk satu bulan tertentu.
    Parameter `bulan` berformat 'YYYY-MM' (contoh: '2026-06').
    """
    conn = get_connection()

    total_pendapatan = conn.execute(
        """SELECT COALESCE(SUM(nilai_omset), 0) AS total
           FROM tb_barang_bawaan
           WHERE tgl_catat LIKE ?""",
        (f"{bulan}%",)
    ).fetchone()["total"]

    total_pengeluaran = conn.execute(
        """SELECT COALESCE(SUM(nominal_biaya), 0) AS total
           FROM tb_pengeluaran
           WHERE tgl_pengeluaran LIKE ?""",
        (f"{bulan}%",)
    ).fetchone()["total"]

    total_gaji = conn.execute(
        """SELECT COALESCE(SUM(jumlah_gaji), 0) AS total
           FROM tb_gaji_harian
           WHERE tgl_gaji LIKE ?""",
        (f"{bulan}%",)
    ).fetchone()["total"]

    conn.close()

    laba_bersih = total_pendapatan - total_pengeluaran - total_gaji

    return {
        "bulan": bulan,
        "total_pendapatan": total_pendapatan,
        "total_pengeluaran": total_pengeluaran,
        "total_gaji": total_gaji,
        "laba_bersih": laba_bersih,
    }
