"""
page_karyawan.py
-------------------------------------------------------------------
Dashboard Karyawan MONIVA (akses terbatas / READ-ONLY).

RBAC pada alur kerja terbaru:
- Karyawan TIDAK memiliki akses untuk menginput atau mengubah data
  barang bawaan maupun gaji. Seluruh pencatatan dilakukan oleh
  Pemilik lewat Dashboard Pemilik (tab "Input Barang Bawaan").
- Karyawan hanya menerima notifikasi & dapat MELIHAT (read-only):
    1. Notifikasi Gaji Transparan -> ringkasan gaji harian, otomatis
       muncul begitu Pemilik menginput data barang bawaan mereka.
    2. Riwayat Barang Bawaan & Performa -> rincian barang yang dibawa,
       terjual, kembali, beserta omset dan gaji yang dihasilkan setiap
       entry, ditampilkan sebagai tabel tanpa kontrol edit apa pun.
-------------------------------------------------------------------
"""

import customtkinter as ctk

import database as db
import theme
from dialog_ganti_password import GantiPasswordDialog


class KaryawanFrame(ctk.CTkFrame):
    """Frame utama Dashboard Karyawan, berisi sidebar + area konten read-only."""

    def __init__(self, master, user_row, on_logout):
        super().__init__(master, fg_color=theme.BG_UTAMA)
        self.user = user_row          # sqlite3.Row berisi data karyawan login
        self.on_logout = on_logout    # callback kembali ke halaman login

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_konten()
        self.refresh_semua_data()

    # ------------------------------------------------------------------
    # SIDEBAR
    # ------------------------------------------------------------------
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=theme.BG_SIDEBAR, width=220, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="🍜 MONIVA",
            font=theme.font_judul(20, "bold"), text_color=theme.MERAH
        ).pack(pady=(28, 0), padx=20)

        ctk.CTkLabel(
            sidebar, text="Bakso Maenyos",
            font=theme.font_kecil(11), text_color=theme.TEKS_MUTED
        ).pack(pady=(0, 24))

        # Kartu identitas pengguna yang sedang login
        kartu_user = ctk.CTkFrame(sidebar, fg_color=theme.BG_KARTU, corner_radius=10)
        kartu_user.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(
            kartu_user, text=self.user["nama"],
            font=theme.font_body(13, "bold"), text_color=theme.TEKS_UTAMA
        ).pack(padx=12, pady=(10, 0), anchor="w")
        ctk.CTkLabel(
            kartu_user, text="Role: Karyawan (Read-only)",
            font=theme.font_kecil(11), text_color=theme.ORANYE
        ).pack(padx=12, pady=(0, 10), anchor="w")

        # Pengisi agar tombol bawah menempel di bawah
        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)

        ctk.CTkButton(
            sidebar, text="🔒 Ganti Password",
            command=self._buka_ganti_password,
            **theme.style_tombol_outline()
        ).pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkButton(
            sidebar, text="Keluar / Logout",
            command=self.on_logout,
            **theme.style_tombol_outline()
        ).pack(fill="x", padx=16, pady=(0, 20))

    def _buka_ganti_password(self):
        """Membuka dialog modal untuk mengganti password akun yang sedang login."""
        GantiPasswordDialog(self, user_row=self.user)

    # ------------------------------------------------------------------
    # AREA KONTEN (scrollable agar aman di layar kecil)
    # ------------------------------------------------------------------
    def _build_konten(self):
        konten = ctk.CTkScrollableFrame(self, fg_color=theme.BG_UTAMA, label_text="")
        konten.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)
        konten.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            konten, text=f"Halo, {self.user['nama']} 👋",
            font=theme.font_judul(22, "bold"), text_color=theme.TEKS_UTAMA
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        ctk.CTkLabel(
            konten,
            text="Halaman ini bersifat lihat-saja (read-only). Data barang bawaan & "
                 "gaji harian Anda diinput oleh Pemilik dan akan muncul otomatis di sini.",
            font=theme.font_body(13), text_color=theme.TEKS_SEKUNDER, wraplength=700, justify="left"
        ).grid(row=1, column=0, sticky="w", pady=(0, 20))

        # --- Kartu Notifikasi Gaji Transparan -----------------------------
        self._build_kartu_gaji(konten, row=2)

        # --- Kartu Riwayat Barang Bawaan & Performa (read-only) -----------
        self._build_riwayat_barang(konten, row=3)

    # ------------------------------------------------------------------
    def _build_kartu_gaji(self, parent, row):
        self.kartu_gaji = ctk.CTkFrame(parent, fg_color=theme.BG_KARTU, corner_radius=theme.RADIUS_KARTU)
        self.kartu_gaji.grid(row=row, column=0, sticky="ew", pady=8)
        self.kartu_gaji.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.kartu_gaji, text="💰 Notifikasi Gaji Transparan",
            font=theme.font_subjudul(16, "bold"), text_color=theme.ORANYE
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            self.kartu_gaji,
            text=(f"Gaji harian ({db.PERSENTASE_GAJI*100:.1f}% dari omset barang bawaan) "
                  "muncul otomatis setiap kali Pemilik menginput data hari itu."),
            font=theme.font_kecil(11), text_color=theme.TEKS_MUTED, wraplength=700, justify="left"
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        # Container daftar gaji - diisi ulang setiap refresh
        self.list_gaji_container = ctk.CTkFrame(self.kartu_gaji, fg_color="transparent")
        self.list_gaji_container.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.list_gaji_container.grid_columnconfigure(0, weight=1)

    def _refresh_kartu_gaji(self):
        for widget in self.list_gaji_container.winfo_children():
            widget.destroy()

        daftar_gaji = db.ambil_gaji_by_user(self.user["id_user"])

        if not daftar_gaji:
            ctk.CTkLabel(
                self.list_gaji_container,
                text="Belum ada gaji yang tercatat. Menunggu input data dari Pemilik.",
                font=theme.font_kecil(12), text_color=theme.TEKS_MUTED, wraplength=700, justify="left"
            ).grid(row=0, column=0, sticky="w")
            return

        total_gaji = sum(g["jumlah_gaji"] for g in daftar_gaji)

        # Ringkasan total di paling atas
        ctk.CTkLabel(
            self.list_gaji_container, text=f"Total Gaji Terkumpul: Rp {total_gaji:,.0f}",
            font=theme.font_body(13, "bold"), text_color=theme.HIJAU_SUKSES
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        for i, gaji in enumerate(daftar_gaji[:6], start=1):  # tampilkan 6 terbaru
            baris = ctk.CTkFrame(self.list_gaji_container, fg_color=theme.BG_INPUT, corner_radius=8)
            baris.grid(row=i, column=0, sticky="ew", pady=4)
            baris.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                baris, text=f"📅 {gaji['tgl_gaji']}",
                font=theme.font_kecil(11), text_color=theme.TEKS_SEKUNDER
            ).grid(row=0, column=0, sticky="w", padx=10, pady=6)

            ctk.CTkLabel(
                baris, text=f"Rp {gaji['jumlah_gaji']:,.0f}",
                font=theme.font_body(13, "bold"), text_color=theme.TEKS_UTAMA
            ).grid(row=0, column=1, sticky="e", padx=10, pady=6)

    # ------------------------------------------------------------------
    def _build_riwayat_barang(self, parent, row):
        kartu = ctk.CTkFrame(parent, fg_color=theme.BG_KARTU, corner_radius=theme.RADIUS_KARTU)
        kartu.grid(row=row, column=0, sticky="ew", pady=8)
        kartu.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            kartu, text="📦 Riwayat Barang Bawaan & Performa Saya",
            font=theme.font_subjudul(16, "bold"), text_color=theme.TEKS_UTAMA
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            kartu,
            text="Data ini diinput oleh Pemilik. Anda hanya dapat melihat, tidak dapat mengubahnya.",
            font=theme.font_kecil(11), text_color=theme.TEKS_MUTED, wraplength=700, justify="left"
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 8))

        # Header tabel manual (CTk tidak punya widget tabel native)
        header = ctk.CTkFrame(kartu, fg_color="transparent")
        header.grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 4))
        judul_kolom = ["Tanggal", "Barang", "Dibawa/Terjual/Kembali", "Omset", "Gaji"]
        for i, judul in enumerate(judul_kolom):
            header.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(
                header, text=judul, font=theme.font_kecil(11, "bold"),
                text_color=theme.TEKS_MUTED
            ).grid(row=0, column=i, sticky="w")

        self.tabel_barang_container = ctk.CTkFrame(kartu, fg_color="transparent")
        self.tabel_barang_container.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.tabel_barang_container.grid_columnconfigure(0, weight=1)

    def _refresh_tabel_barang(self):
        for widget in self.tabel_barang_container.winfo_children():
            widget.destroy()

        daftar = db.ambil_barang_by_user(self.user["id_user"])

        if not daftar:
            ctk.CTkLabel(
                self.tabel_barang_container, text="Belum ada riwayat barang bawaan.",
                font=theme.font_kecil(12), text_color=theme.TEKS_MUTED
            ).grid(row=0, column=0, sticky="w", pady=8)
            return

        for i, b in enumerate(daftar):
            baris = ctk.CTkFrame(self.tabel_barang_container, fg_color=theme.BG_INPUT, corner_radius=6)
            baris.grid(row=i, column=0, sticky="ew", pady=3)
            for col in range(5):
                baris.grid_columnconfigure(col, weight=1)

            gaji_entry = b["nilai_omset"] * db.PERSENTASE_GAJI

            ctk.CTkLabel(
                baris, text=b["tgl_catat"], font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER
            ).grid(row=0, column=0, sticky="w", padx=10, pady=8)

            ctk.CTkLabel(
                baris, text=b["nama_barang"], font=theme.font_body(12, "bold"), text_color=theme.TEKS_UTAMA
            ).grid(row=0, column=1, sticky="w", padx=10, pady=8)

            ctk.CTkLabel(
                baris, text=f"{b['jumlah_dibawa']} / {b['jumlah_terjual']} / {b['jumlah_kembali']}",
                font=theme.font_kecil(11), text_color=theme.TEKS_SEKUNDER
            ).grid(row=0, column=2, sticky="w", padx=10, pady=8)

            ctk.CTkLabel(
                baris, text=f"Rp {b['nilai_omset']:,.0f}",
                font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER
            ).grid(row=0, column=3, sticky="w", padx=10, pady=8)

            ctk.CTkLabel(
                baris, text=f"Rp {gaji_entry:,.0f}",
                font=theme.font_body(12, "bold"), text_color=theme.HIJAU_SUKSES
            ).grid(row=0, column=4, sticky="w", padx=10, pady=8)

    # ------------------------------------------------------------------
    def refresh_semua_data(self):
        """Dipanggil setiap kali data berubah agar seluruh kartu sinkron."""
        self._refresh_kartu_gaji()
        self._refresh_tabel_barang()
