"""
page_pemilik.py
-------------------------------------------------------------------
Dashboard Pemilik MONIVA (akses penuh).

Fitur:
1. Input Barang Bawaan (MULTI-BARANG per sesi) — REVISI UTAMA:
   - Nama Barang diubah menjadi Dropdown dari master daftar barang.
   - Satu form/entry (1 hari) bisa menampung BEBERAPA jenis barang
     menggunakan sistem "Tambah Baris" (dynamic rows).
   - Setiap baris: Pilih Barang (dropdown) | Dibawa | Kembali | Terjual (otomatis) | Omset (otomatis).
   - Omset per baris = (Dibawa - Kembali) x Harga Satuan Barang.
   - Total Omset Harian = penjumlahan omset semua baris.
   - Gaji Karyawan = Total Omset Harian x 17.5%.
2. Form Input Pengeluaran.
3. Dasbor Real-time Finansial (grafik matplotlib).
4. Ekspor Laporan Laba Rugi bulanan (.txt / .csv).
-------------------------------------------------------------------
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from datetime import date
import csv
import os

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import database as db
import theme
from dialog_ganti_password import GantiPasswordDialog


class PemilikFrame(ctk.CTkFrame):
    """Frame utama Dashboard Pemilik, berisi sidebar + tab-tab konten."""

    def __init__(self, master, user_row, on_logout):
        super().__init__(master, fg_color=theme.BG_UTAMA)
        self.user = user_row
        self.on_logout = on_logout

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_tabview()
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

        kartu_user = ctk.CTkFrame(sidebar, fg_color=theme.BG_KARTU, corner_radius=10)
        kartu_user.pack(fill="x", padx=16, pady=8)
        ctk.CTkLabel(
            kartu_user, text=self.user["nama"],
            font=theme.font_body(13, "bold"), text_color=theme.TEKS_UTAMA
        ).pack(padx=12, pady=(10, 0), anchor="w")
        ctk.CTkLabel(
            kartu_user, text="Role: Pemilik",
            font=theme.font_kecil(11), text_color=theme.ORANYE
        ).pack(padx=12, pady=(0, 10), anchor="w")

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
        GantiPasswordDialog(self, user_row=self.user)

    # ------------------------------------------------------------------
    # TABVIEW
    # ------------------------------------------------------------------
    def _build_tabview(self):
        self.tabview = ctk.CTkTabview(
            self, fg_color=theme.BG_UTAMA,
            segmented_button_fg_color=theme.BG_KARTU,
            segmented_button_selected_color=theme.MERAH,
            segmented_button_selected_hover_color=theme.MERAH_HOVER,
            segmented_button_unselected_color=theme.BG_KARTU,
            text_color=theme.TEKS_UTAMA,
            corner_radius=theme.RADIUS_KARTU,
        )
        self.tabview.grid(row=0, column=1, sticky="nsew", padx=24, pady=24)

        tab_dasbor = self.tabview.add("📊 Dasbor Finansial")
        tab_barang = self.tabview.add("📦 Input Barang Bawaan")
        tab_pengeluaran = self.tabview.add("💸 Input Pengeluaran")
        tab_ekspor = self.tabview.add("📁 Ekspor Laporan")

        for tab in (tab_dasbor, tab_barang, tab_pengeluaran, tab_ekspor):
            tab.grid_columnconfigure(0, weight=1)

        self._build_tab_dasbor(tab_dasbor)
        self._build_tab_barang_bawaan(tab_barang)
        self._build_tab_pengeluaran(tab_pengeluaran)
        self._build_tab_ekspor(tab_ekspor)

    # ==================================================================
    # TAB 1: DASBOR REAL-TIME FINANSIAL
    # ==================================================================
    def _build_tab_dasbor(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            scroll, text="Ringkasan Finansial Real-time",
            font=theme.font_subjudul(18, "bold"), text_color=theme.TEKS_UTAMA
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(4, 16))

        self.kartu_omset = self._kartu_metrik(scroll, "Total Pendapatan (Verified)", theme.HIJAU_SUKSES)
        self.kartu_omset.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=8)

        self.kartu_pengeluaran = self._kartu_metrik(scroll, "Total Pengeluaran", theme.MERAH_GAGAL)
        self.kartu_pengeluaran.grid(row=1, column=1, sticky="ew", padx=8, pady=8)

        self.kartu_laba = self._kartu_metrik(scroll, "Estimasi Laba Bersih", theme.ORANYE)
        self.kartu_laba.grid(row=1, column=2, sticky="ew", padx=(8, 0), pady=8)

        kartu_grafik = ctk.CTkFrame(scroll, fg_color=theme.BG_KARTU, corner_radius=theme.RADIUS_KARTU)
        kartu_grafik.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(8, 0))
        kartu_grafik.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            kartu_grafik, text="📈 Tren Pendapatan vs Pengeluaran",
            font=theme.font_subjudul(15, "bold"), text_color=theme.TEKS_UTAMA
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        self.grafik_container = ctk.CTkFrame(kartu_grafik, fg_color=theme.BG_KARTU)
        self.grafik_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 16))
        self.canvas_grafik = None

    def _kartu_metrik(self, parent, label, warna_aksen):
        kartu = ctk.CTkFrame(parent, fg_color=theme.BG_KARTU, corner_radius=theme.RADIUS_KARTU)
        ctk.CTkLabel(
            kartu, text=label, font=theme.font_kecil(11), text_color=theme.TEKS_MUTED
        ).pack(anchor="w", padx=18, pady=(16, 2))
        nilai_label = ctk.CTkLabel(
            kartu, text="Rp 0", font=theme.font_judul(22, "bold"), text_color=warna_aksen
        )
        nilai_label.pack(anchor="w", padx=18, pady=(0, 16))
        kartu.nilai_label = nilai_label
        return kartu

    def _refresh_dasbor(self):
        omset_data = db.rekap_omset_per_tanggal()
        pengeluaran_data = db.rekap_pengeluaran_per_tanggal()

        total_omset = sum(nilai for _, nilai in omset_data)
        total_pengeluaran = sum(nilai for _, nilai in pengeluaran_data)
        laba_bersih = total_omset - total_pengeluaran

        self.kartu_omset.nilai_label.configure(text=f"Rp {total_omset:,.0f}")
        self.kartu_pengeluaran.nilai_label.configure(text=f"Rp {total_pengeluaran:,.0f}")
        warna_laba = theme.HIJAU_SUKSES if laba_bersih >= 0 else theme.MERAH_GAGAL
        self.kartu_laba.nilai_label.configure(text=f"Rp {laba_bersih:,.0f}", text_color=warna_laba)

        self._gambar_grafik(omset_data, pengeluaran_data)

    def _gambar_grafik(self, omset_data, pengeluaran_data):
        if self.canvas_grafik is not None:
            self.canvas_grafik.get_tk_widget().destroy()

        semua_tanggal = sorted(set([t for t, _ in omset_data] + [t for t, _ in pengeluaran_data]))
        map_omset = dict(omset_data)
        map_pengeluaran = dict(pengeluaran_data)
        y_omset = [map_omset.get(t, 0) for t in semua_tanggal]
        y_pengeluaran = [map_pengeluaran.get(t, 0) for t in semua_tanggal]

        fig = Figure(figsize=(7.5, 3.4), dpi=100, facecolor=theme.BG_KARTU)
        ax = fig.add_subplot(111)
        ax.set_facecolor(theme.BG_KARTU)

        if not semua_tanggal:
            ax.text(0.5, 0.5, "Belum ada data transaksi",
                     ha="center", va="center", color=theme.TEKS_MUTED, fontsize=11,
                     transform=ax.transAxes)
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            ax.plot(semua_tanggal, y_omset, marker="o", color=theme.ORANYE,
                    linewidth=2.2, label="Pendapatan")
            ax.plot(semua_tanggal, y_pengeluaran, marker="o", color=theme.MERAH,
                    linewidth=2.2, label="Pengeluaran")
            ax.fill_between(semua_tanggal, y_omset, color=theme.ORANYE, alpha=0.08)
            ax.fill_between(semua_tanggal, y_pengeluaran, color=theme.MERAH, alpha=0.08)

            ax.legend(facecolor=theme.BG_KARTU, edgecolor=theme.BG_KARTU,
                      labelcolor=theme.TEKS_UTAMA, fontsize=9, loc="upper left")
            ax.tick_params(axis="x", colors=theme.TEKS_SEKUNDER, labelsize=8)
            ax.tick_params(axis="y", colors=theme.TEKS_SEKUNDER, labelsize=8)
            for label in ax.get_xticklabels():
                label.set_rotation(20)
                label.set_ha("right")

        for spine in ax.spines.values():
            spine.set_color(theme.BG_INPUT)

        fig.tight_layout(pad=1.5)

        self.canvas_grafik = FigureCanvasTkAgg(fig, master=self.grafik_container)
        self.canvas_grafik.draw()
        self.canvas_grafik.get_tk_widget().pack(fill="both", expand=True)

    # ==================================================================
    # TAB 2: INPUT BARANG BAWAAN — MULTI-BARANG (DYNAMIC ROWS)
    # ==================================================================
    def _build_tab_barang_bawaan(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            scroll, text="📦 Input Barang Bawaan Karyawan",
            font=theme.font_subjudul(18, "bold"), text_color=theme.TEKS_UTAMA
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(4, 4))

        ctk.CTkLabel(
            scroll,
            text=(
                "Hanya Pemilik yang dapat menginput data ini. "
                "Tambahkan beberapa jenis barang sekaligus, omset dihitung otomatis per baris. "
                f"Gaji karyawan ({db.PERSENTASE_GAJI*100:.1f}% dari total omset) "
                "otomatis tersimpan setelah klik Simpan."
            ),
            font=theme.font_kecil(12), text_color=theme.TEKS_MUTED,
            wraplength=680, justify="left"
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 16))

        # --- Kartu Form (kiri) -----------------------------------------
        kartu_form = ctk.CTkFrame(scroll, fg_color=theme.BG_KARTU, corner_radius=theme.RADIUS_KARTU)
        kartu_form.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=4)
        kartu_form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            kartu_form, text="Catat Barang Bawaan Hari Ini",
            font=theme.font_subjudul(15, "bold"), text_color=theme.MERAH
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 12))

        # --- Pilih Karyawan ---
        ctk.CTkLabel(
            kartu_form, text="Karyawan", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=1, column=0, sticky="w", padx=20)

        daftar_karyawan = db.ambil_daftar_karyawan()
        self._map_nama_ke_id = {f"{k['nama']} ({k['username']})": k["id_user"] for k in daftar_karyawan}
        nilai_dropdown = list(self._map_nama_ke_id.keys()) or ["Belum ada akun Karyawan"]

        self.combo_karyawan = ctk.CTkComboBox(
            kartu_form, values=nilai_dropdown,
            corner_radius=theme.RADIUS_TOMBOL, height=theme.TINGGI_INPUT,
            fg_color=theme.BG_INPUT, border_color=theme.ORANYE_TUA,
            button_color=theme.ORANYE_TUA, button_hover_color=theme.ORANYE_HOVER,
            text_color=theme.TEKS_UTAMA, dropdown_fg_color=theme.BG_INPUT,
            dropdown_text_color=theme.TEKS_UTAMA,
        )
        self.combo_karyawan.set(nilai_dropdown[0])
        self.combo_karyawan.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 12))

        # --- Tanggal ---
        ctk.CTkLabel(
            kartu_form, text="Tanggal Catat (YYYY-MM-DD)", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=3, column=0, sticky="w", padx=20)
        self.entry_tgl_barang = ctk.CTkEntry(kartu_form, **theme.style_input())
        self.entry_tgl_barang.insert(0, date.today().isoformat())
        self.entry_tgl_barang.grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 16))

        # --- Header baris barang ---
        header_baris = ctk.CTkFrame(kartu_form, fg_color="transparent")
        header_baris.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 4))
        header_baris.grid_columnconfigure(0, weight=3)  # Nama Barang
        header_baris.grid_columnconfigure(1, weight=1)  # Dibawa
        header_baris.grid_columnconfigure(2, weight=1)  # Kembali
        header_baris.grid_columnconfigure(3, weight=1)  # Terjual
        header_baris.grid_columnconfigure(4, weight=2)  # Omset
        header_baris.grid_columnconfigure(5, minsize=32) # Hapus

        for col, teks in enumerate(["Nama Barang", "Dibawa", "Kembali", "Terjual*", "Omset (Rp)*"]):
            ctk.CTkLabel(
                header_baris, text=teks,
                font=theme.font_kecil(10, "bold"), text_color=theme.TEKS_MUTED, anchor="w"
            ).grid(row=0, column=col, sticky="w", padx=(0 if col > 0 else 0, 4))

        # --- Container baris-baris barang (dynamic) ---
        self._baris_barang = []  # list of dict per baris widget

        self.container_baris = ctk.CTkFrame(kartu_form, fg_color="transparent")
        self.container_baris.grid(row=6, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.container_baris.grid_columnconfigure(0, weight=1)

        # Mulai dengan 1 baris kosong
        self._tambah_baris_barang()

        # --- Tombol Tambah Baris ---
        ctk.CTkButton(
            kartu_form, text="＋ Tambah Baris Barang", width=220,
            command=self._tambah_baris_barang,
            **theme.style_tombol_sekunder()
        ).grid(row=7, column=0, sticky="w", padx=20, pady=(0, 12))

        # --- Ringkasan total & preview gaji ---
        frame_total = ctk.CTkFrame(kartu_form, fg_color=theme.BG_INPUT, corner_radius=8)
        frame_total.grid(row=8, column=0, sticky="ew", padx=20, pady=(0, 12))
        frame_total.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame_total, text="Total Omset Harian:",
            font=theme.font_body(13), text_color=theme.TEKS_SEKUNDER
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))
        self.label_total_omset = ctk.CTkLabel(
            frame_total, text="Rp 0",
            font=theme.font_body(14, "bold"), text_color=theme.ORANYE
        )
        self.label_total_omset.grid(row=0, column=1, sticky="e", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            frame_total, text=f"Estimasi Gaji ({db.PERSENTASE_GAJI*100:.1f}%):",
            font=theme.font_body(13), text_color=theme.TEKS_SEKUNDER
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(2, 10))
        self.label_preview_gaji = ctk.CTkLabel(
            frame_total, text="Rp 0",
            font=theme.font_body(14, "bold"), text_color=theme.HIJAU_SUKSES
        )
        self.label_preview_gaji.grid(row=1, column=1, sticky="e", padx=14, pady=(2, 10))

        ctk.CTkButton(
            kartu_form, text="💾 Simpan & Hitung Gaji Otomatis",
            command=self._proses_simpan_barang_bawaan,
            **theme.style_tombol_primer()
        ).grid(row=9, column=0, sticky="ew", padx=20, pady=(0, 20))

        # --- Riwayat Barang Bawaan (kanan) ---
        kartu_riwayat = ctk.CTkFrame(scroll, fg_color=theme.BG_KARTU, corner_radius=theme.RADIUS_KARTU)
        kartu_riwayat.grid(row=2, column=1, sticky="nsew", padx=(10, 0), pady=4)
        kartu_riwayat.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            kartu_riwayat, text="📜 Riwayat Barang Bawaan",
            font=theme.font_subjudul(15, "bold"), text_color=theme.TEKS_UTAMA
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 12))

        self.container_riwayat_barang = ctk.CTkFrame(kartu_riwayat, fg_color="transparent")
        self.container_riwayat_barang.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.container_riwayat_barang.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # DYNAMIC ROWS — Sistem Tambah/Hapus Baris Barang
    # ------------------------------------------------------------------
    def _tambah_baris_barang(self):
        """Menambahkan satu baris input barang baru ke container."""
        idx = len(self._baris_barang)
        nama_barang_list = list(db.MASTER_BARANG.keys())

        frame_baris = ctk.CTkFrame(self.container_baris, fg_color=theme.BG_INPUT, corner_radius=6)
        frame_baris.grid(row=idx, column=0, sticky="ew", pady=3)
        frame_baris.grid_columnconfigure(0, weight=3)
        frame_baris.grid_columnconfigure(1, weight=1)
        frame_baris.grid_columnconfigure(2, weight=1)
        frame_baris.grid_columnconfigure(3, weight=1)
        frame_baris.grid_columnconfigure(4, weight=2)
        frame_baris.grid_columnconfigure(5, minsize=36)

        # Dropdown nama barang
        combo_barang = ctk.CTkComboBox(
            frame_baris,
            values=nama_barang_list,
            corner_radius=6, height=34,
            fg_color=theme.BG_KARTU, border_color=theme.ORANYE_TUA,
            button_color=theme.ORANYE_TUA, button_hover_color=theme.ORANYE_HOVER,
            text_color=theme.TEKS_UTAMA, dropdown_fg_color=theme.BG_KARTU,
            dropdown_text_color=theme.TEKS_UTAMA,
            font=theme.font_body(12),
        )
        combo_barang.set(nama_barang_list[0])
        combo_barang.grid(row=0, column=0, sticky="ew", padx=(6, 3), pady=6)

        # Input Dibawa
        entry_dibawa = ctk.CTkEntry(
            frame_baris, placeholder_text="0", width=60,
            corner_radius=6, height=34,
            fg_color=theme.BG_KARTU, border_color=theme.ORANYE_TUA,
            text_color=theme.TEKS_UTAMA, font=theme.font_body(12),
        )
        entry_dibawa.grid(row=0, column=1, sticky="ew", padx=3, pady=6)

        # Input Kembali
        entry_kembali = ctk.CTkEntry(
            frame_baris, placeholder_text="0", width=60,
            corner_radius=6, height=34,
            fg_color=theme.BG_KARTU, border_color=theme.ORANYE_TUA,
            text_color=theme.TEKS_UTAMA, font=theme.font_body(12),
        )
        entry_kembali.grid(row=0, column=2, sticky="ew", padx=3, pady=6)

        # Label Terjual (read-only, otomatis = Dibawa - Kembali)
        label_terjual = ctk.CTkLabel(
            frame_baris, text="0",
            font=theme.font_body(12, "bold"), text_color=theme.TEKS_UTAMA,
            anchor="center",
        )
        label_terjual.grid(row=0, column=3, sticky="ew", padx=3, pady=6)

        # Label Omset (read-only, otomatis)
        label_omset = ctk.CTkLabel(
            frame_baris, text="Rp 0",
            font=theme.font_body(12, "bold"), text_color=theme.ORANYE,
            anchor="w",
        )
        label_omset.grid(row=0, column=4, sticky="ew", padx=(3, 0), pady=6)

        # Tombol hapus baris
        btn_hapus = ctk.CTkButton(
            frame_baris, text="✕", width=30, height=30,
            corner_radius=6,
            fg_color="transparent", hover_color=theme.MERAH_TUA,
            text_color=theme.MERAH_GAGAL, font=theme.font_body(13, "bold"),
            command=lambda f=frame_baris, i=idx: self._hapus_baris_barang(f),
        )
        btn_hapus.grid(row=0, column=5, padx=(3, 6), pady=6)

        data_baris = {
            "frame": frame_baris,
            "combo_barang": combo_barang,
            "entry_dibawa": entry_dibawa,
            "entry_kembali": entry_kembali,
            "label_terjual": label_terjual,
            "label_omset": label_omset,
        }
        self._baris_barang.append(data_baris)

        # Bind perubahan input agar terjual & omset dihitung ulang otomatis
        def on_change(event=None, d=data_baris):
            self._hitung_baris(d)
            self._update_total_preview()

        combo_barang.configure(command=lambda val, d=data_baris: on_change())
        entry_dibawa.bind("<KeyRelease>", on_change)
        entry_kembali.bind("<KeyRelease>", on_change)

        self._update_total_preview()

    def _hapus_baris_barang(self, frame_target):
        """Menghapus satu baris barang dari daftar dan menyembunyikan frame-nya."""
        # Jangan hapus jika hanya tersisa 1 baris
        aktif = [b for b in self._baris_barang if b["frame"].winfo_exists()]
        if len(aktif) <= 1:
            messagebox.showwarning("MONIVA", "Minimal harus ada 1 baris barang.")
            return

        for b in self._baris_barang:
            if b["frame"] is frame_target:
                b["frame"].destroy()
                break

        # Bersihkan entri yang sudah dihapus dari list
        self._baris_barang = [b for b in self._baris_barang if b["frame"].winfo_exists()]
        self._update_total_preview()

    def _hitung_baris(self, data_baris):
        """Menghitung terjual & omset untuk satu baris, lalu update label."""
        try:
            dibawa = int(data_baris["entry_dibawa"].get().strip() or "0")
        except ValueError:
            dibawa = 0
        try:
            kembali = int(data_baris["entry_kembali"].get().strip() or "0")
        except ValueError:
            kembali = 0

        terjual = max(0, dibawa - kembali)
        nama_barang = data_baris["combo_barang"].get()
        harga = db.MASTER_BARANG.get(nama_barang, 0)
        omset = terjual * harga

        data_baris["label_terjual"].configure(text=str(terjual))
        data_baris["label_omset"].configure(text=f"Rp {omset:,.0f}")

    def _update_total_preview(self):
        """Menjumlahkan omset semua baris lalu update label total & preview gaji."""
        total = 0
        for b in self._baris_barang:
            if not b["frame"].winfo_exists():
                continue
            try:
                dibawa = int(b["entry_dibawa"].get().strip() or "0")
            except ValueError:
                dibawa = 0
            try:
                kembali = int(b["entry_kembali"].get().strip() or "0")
            except ValueError:
                kembali = 0
            terjual = max(0, dibawa - kembali)
            harga = db.MASTER_BARANG.get(b["combo_barang"].get(), 0)
            total += terjual * harga

        gaji = total * db.PERSENTASE_GAJI
        if hasattr(self, "label_total_omset"):
            self.label_total_omset.configure(text=f"Rp {total:,.0f}")
        if hasattr(self, "label_preview_gaji"):
            self.label_preview_gaji.configure(text=f"Rp {gaji:,.0f}")

    def _proses_simpan_barang_bawaan(self):
        """
        Validasi seluruh input multi-baris, lalu simpan sekaligus dan
        hitung gaji harian karyawan dari TOTAL omset semua baris (1 langkah).
        """
        nama_pilihan = self.combo_karyawan.get().strip()
        id_karyawan = self._map_nama_ke_id.get(nama_pilihan)
        if id_karyawan is None:
            messagebox.showwarning("MONIVA", "Pilih karyawan yang valid terlebih dahulu.")
            return

        tgl = self.entry_tgl_barang.get().strip()
        try:
            date.fromisoformat(tgl)
        except ValueError:
            messagebox.showwarning("MONIVA", "Format tanggal harus YYYY-MM-DD, contoh: 2026-06-22.")
            return

        # Kumpulkan & validasi semua baris aktif
        baris_aktif = [b for b in self._baris_barang if b["frame"].winfo_exists()]
        if not baris_aktif:
            messagebox.showwarning("MONIVA", "Minimal harus ada 1 baris barang.")
            return

        daftar_barang = []
        for i, b in enumerate(baris_aktif, start=1):
            nama_barang = b["combo_barang"].get().strip()
            if not nama_barang or nama_barang not in db.MASTER_BARANG:
                messagebox.showwarning("MONIVA", f"Baris {i}: Pilih nama barang yang valid.")
                return

            try:
                dibawa = int(b["entry_dibawa"].get().strip())
                kembali = int(b["entry_kembali"].get().strip())
                if dibawa < 0 or kembali < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "MONIVA", f"Baris {i}: Jumlah Dibawa & Kembali harus berupa angka bulat ≥ 0."
                )
                return

            if kembali > dibawa:
                messagebox.showwarning(
                    "MONIVA",
                    f"Baris {i} ({nama_barang}): Jumlah Kembali ({kembali}) "
                    f"tidak boleh melebihi Jumlah Dibawa ({dibawa})."
                )
                return

            terjual = dibawa - kembali
            harga_satuan = db.MASTER_BARANG[nama_barang]
            nilai_omset = terjual * harga_satuan

            daftar_barang.append({
                "nama_barang": nama_barang,
                "harga_satuan": harga_satuan,
                "jumlah_dibawa": dibawa,
                "jumlah_terjual": terjual,
                "jumlah_kembali": kembali,
                "nilai_omset": nilai_omset,
            })

        # Simpan ke database (multi-barang, 1 sesi, 1 entri gaji)
        total_omset, jumlah_gaji = db.tambah_barang_bawaan_multi(
            tgl_catat=tgl,
            id_user=id_karyawan,
            daftar_barang=daftar_barang,
            id_user_pencatat=self.user["id_user"],
        )

        jumlah_barang = len(daftar_barang)
        messagebox.showinfo(
            "MONIVA",
            f"✅ {jumlah_barang} jenis barang berhasil disimpan.\n\n"
            f"Total Omset Harian : Rp {total_omset:,.0f}\n"
            f"Gaji '{nama_pilihan}' : Rp {jumlah_gaji:,.0f}"
        )

        # Reset form: hapus semua baris lama, mulai lagi dengan 1 baris kosong
        for b in self._baris_barang:
            if b["frame"].winfo_exists():
                b["frame"].destroy()
        self._baris_barang.clear()
        self._tambah_baris_barang()
        self._update_total_preview()

        self.refresh_semua_data()

    def _refresh_barang_bawaan(self):
        for widget in self.container_riwayat_barang.winfo_children():
            widget.destroy()

        daftar = db.ambil_semua_barang_bawaan()
        if not daftar:
            ctk.CTkLabel(
                self.container_riwayat_barang, text="Belum ada data barang bawaan.",
                font=theme.font_body(13), text_color=theme.TEKS_MUTED
            ).grid(row=0, column=0, sticky="w")
            return

        for i, b in enumerate(daftar[:15]):
            baris = ctk.CTkFrame(self.container_riwayat_barang, fg_color=theme.BG_INPUT, corner_radius=6)
            baris.grid(row=i, column=0, sticky="ew", pady=3)
            baris.grid_columnconfigure(0, weight=1)

            harga_satuan = b["harga_satuan"] if b["harga_satuan"] else db.MASTER_BARANG.get(b["nama_barang"], 0)

            ctk.CTkLabel(
                baris,
                text=f"{b['tgl_catat']} • {b['nama_karyawan']} • {b['nama_barang']}",
                font=theme.font_body(12, "bold"), text_color=theme.TEKS_UTAMA
            ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))

            gaji_entry = b["nilai_omset"] * db.PERSENTASE_GAJI
            ctk.CTkLabel(
                baris,
                text=(
                    f"Dibawa {b['jumlah_dibawa']} • Terjual {b['jumlah_terjual']} • "
                    f"Kembali {b['jumlah_kembali']}  |  "
                    f"@Rp {harga_satuan:,.0f}  |  "
                    f"Omset Rp {b['nilai_omset']:,.0f}"
                ),
                font=theme.font_kecil(11), text_color=theme.ORANYE
            ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

    # ==================================================================
    # TAB 3: FORM INPUT PENGELUARAN
    # ==================================================================
    def _build_tab_pengeluaran(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        kartu_form = ctk.CTkFrame(scroll, fg_color=theme.BG_KARTU, corner_radius=theme.RADIUS_KARTU)
        kartu_form.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=4)
        kartu_form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            kartu_form, text="💸 Input Pengeluaran Baru",
            font=theme.font_subjudul(16, "bold"), text_color=theme.MERAH
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            kartu_form, text="Tanggal Pengeluaran (YYYY-MM-DD)", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER
        ).grid(row=1, column=0, sticky="w", padx=20)
        self.entry_tgl_pengeluaran = ctk.CTkEntry(kartu_form, **theme.style_input())
        self.entry_tgl_pengeluaran.insert(0, date.today().isoformat())
        self.entry_tgl_pengeluaran.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 12))

        ctk.CTkLabel(
            kartu_form, text="Kategori Biaya", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER
        ).grid(row=3, column=0, sticky="w", padx=20)
        self.combo_kategori = ctk.CTkComboBox(
            kartu_form, values=["Bahan Baku", "Energi", "Operasional"],
            corner_radius=theme.RADIUS_TOMBOL, height=theme.TINGGI_INPUT,
            fg_color=theme.BG_INPUT, border_color=theme.ORANYE_TUA,
            button_color=theme.ORANYE_TUA, button_hover_color=theme.ORANYE_HOVER,
            text_color=theme.TEKS_UTAMA, dropdown_fg_color=theme.BG_INPUT,
            dropdown_text_color=theme.TEKS_UTAMA,
        )
        self.combo_kategori.set("Bahan Baku")
        self.combo_kategori.grid(row=4, column=0, sticky="ew", padx=20, pady=(4, 12))

        ctk.CTkLabel(
            kartu_form, text="Nama Barang / Kegiatan", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER
        ).grid(row=5, column=0, sticky="w", padx=20)
        self.entry_nama_item = ctk.CTkEntry(
            kartu_form, placeholder_text="Contoh: Daging, Bensin Pegawai, Listrik",
            **theme.style_input()
        )
        self.entry_nama_item.grid(row=6, column=0, sticky="ew", padx=20, pady=(4, 12))

        ctk.CTkLabel(
            kartu_form, text="Nominal Pengeluaran (Rp)", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER
        ).grid(row=7, column=0, sticky="w", padx=20)
        self.entry_nominal_pengeluaran = ctk.CTkEntry(
            kartu_form, placeholder_text="Contoh: 150000", **theme.style_input()
        )
        self.entry_nominal_pengeluaran.grid(row=8, column=0, sticky="ew", padx=20, pady=(4, 12))

        ctk.CTkLabel(
            kartu_form, text="Foto Nota", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER
        ).grid(row=9, column=0, sticky="w", padx=20)

        baris_unggah = ctk.CTkFrame(kartu_form, fg_color="transparent")
        baris_unggah.grid(row=10, column=0, sticky="ew", padx=20, pady=(4, 16))
        baris_unggah.grid_columnconfigure(0, weight=1)

        self.label_path_nota = ctk.CTkLabel(
            baris_unggah, text="Belum ada file dipilih", anchor="w",
            font=theme.font_kecil(11), text_color=theme.TEKS_MUTED
        )
        self.label_path_nota.grid(row=0, column=0, sticky="ew")
        self.path_nota_terpilih = ""

        ctk.CTkButton(
            baris_unggah, text="Pilih Foto", width=100,
            command=self._proses_pilih_foto_nota,
            **theme.style_tombol_sekunder()
        ).grid(row=0, column=1, padx=(8, 0))

        ctk.CTkButton(
            kartu_form, text="Simpan Pengeluaran",
            command=self._proses_input_pengeluaran,
            **theme.style_tombol_primer()
        ).grid(row=11, column=0, sticky="ew", padx=20, pady=(0, 20))

        kartu_riwayat = ctk.CTkFrame(scroll, fg_color=theme.BG_KARTU, corner_radius=theme.RADIUS_KARTU)
        kartu_riwayat.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=4)
        kartu_riwayat.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            kartu_riwayat, text="📜 Riwayat Pengeluaran",
            font=theme.font_subjudul(16, "bold"), text_color=theme.TEKS_UTAMA
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 12))

        self.container_riwayat_pengeluaran = ctk.CTkFrame(kartu_riwayat, fg_color="transparent")
        self.container_riwayat_pengeluaran.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        self.container_riwayat_pengeluaran.grid_columnconfigure(0, weight=1)

    def _proses_pilih_foto_nota(self):
        path = filedialog.askopenfilename(
            title="Pilih Foto Nota",
            filetypes=[("Gambar", "*.jpg *.jpeg *.png"), ("Semua file", "*.*")]
        )
        if path:
            self.path_nota_terpilih = path
            nama_file = os.path.basename(path)
            self.label_path_nota.configure(text=f"📎 {nama_file}", text_color=theme.HIJAU_SUKSES)

    def _proses_input_pengeluaran(self):
        tgl = self.entry_tgl_pengeluaran.get().strip()
        kategori = self.combo_kategori.get().strip()
        nama_item = self.entry_nama_item.get().strip()
        nominal_teks = self.entry_nominal_pengeluaran.get().strip()

        if not tgl:
            messagebox.showwarning("MONIVA", "Tanggal pengeluaran wajib diisi.")
            return
        try:
            date.fromisoformat(tgl)
        except ValueError:
            messagebox.showwarning("MONIVA", "Format tanggal harus YYYY-MM-DD, contoh: 2026-06-22.")
            return
        if not kategori:
            messagebox.showwarning("MONIVA", "Kategori biaya wajib dipilih.")
            return
        if not nama_item:
            messagebox.showwarning("MONIVA", "Nama barang/kegiatan wajib diisi, contoh: Daging atau Bensin Pegawai.")
            return
        try:
            nominal = float(nominal_teks)
            if nominal <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("MONIVA", "Nominal pengeluaran harus berupa angka positif.")
            return

        db.tambah_pengeluaran(tgl, kategori, nama_item, nominal, self.path_nota_terpilih, self.user["id_user"])
        messagebox.showinfo("MONIVA", "Data pengeluaran berhasil disimpan.")

        self.entry_nama_item.delete(0, "end")
        self.entry_nominal_pengeluaran.delete(0, "end")
        self.path_nota_terpilih = ""
        self.label_path_nota.configure(text="Belum ada file dipilih", text_color=theme.TEKS_MUTED)

        self.refresh_semua_data()

    def _refresh_pengeluaran(self):
        for widget in self.container_riwayat_pengeluaran.winfo_children():
            widget.destroy()

        daftar = db.ambil_semua_pengeluaran()
        if not daftar:
            ctk.CTkLabel(
                self.container_riwayat_pengeluaran, text="Belum ada data pengeluaran.",
                font=theme.font_body(13), text_color=theme.TEKS_MUTED
            ).grid(row=0, column=0, sticky="w")
            return

        for i, p in enumerate(daftar[:15]):
            baris = ctk.CTkFrame(self.container_riwayat_pengeluaran, fg_color=theme.BG_INPUT, corner_radius=6)
            baris.grid(row=i, column=0, sticky="ew", pady=3)
            baris.grid_columnconfigure(0, weight=1)

            nama_item = p["nama_item"] if p["nama_item"] else "(tanpa nama)"
            ctk.CTkLabel(
                baris, text=f"{p['tgl_pengeluaran']} • {p['kategori_biaya']} • {nama_item}",
                font=theme.font_body(12, "bold"), text_color=theme.TEKS_UTAMA
            ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))

            keterangan_nota = "📎 ada nota" if p["foto_nota"] else "tanpa nota"
            ctk.CTkLabel(
                baris, text=f"Rp {p['nominal_biaya']:,.0f}  •  {keterangan_nota}",
                font=theme.font_kecil(11), text_color=theme.ORANYE
            ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

    # ==================================================================
    # TAB 4: EKSPOR LAPORAN LABA RUGI
    # ==================================================================
    def _build_tab_ekspor(self, tab):
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        kartu = ctk.CTkFrame(scroll, fg_color=theme.BG_KARTU, corner_radius=theme.RADIUS_KARTU)
        kartu.grid(row=0, column=0, sticky="ew", pady=4)
        kartu.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            kartu, text="📁 Ekspor Laporan Laba Rugi Bulanan",
            font=theme.font_subjudul(16, "bold"), text_color=theme.MERAH
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 12))

        ctk.CTkLabel(
            kartu, text="Pilih bulan (format YYYY-MM) yang ingin direkap, lalu pilih format ekspor.",
            font=theme.font_kecil(12), text_color=theme.TEKS_MUTED
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        self.entry_bulan_ekspor = ctk.CTkEntry(
            kartu, placeholder_text=date.today().strftime("%Y-%m"), **theme.style_input()
        )
        self.entry_bulan_ekspor.insert(0, date.today().strftime("%Y-%m"))
        self.entry_bulan_ekspor.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        baris_tombol = ctk.CTkFrame(kartu, fg_color="transparent")
        baris_tombol.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 12))
        baris_tombol.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            baris_tombol, text="Ekspor sebagai .TXT",
            command=lambda: self._proses_ekspor("txt"),
            **theme.style_tombol_primer()
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ctk.CTkButton(
            baris_tombol, text="Ekspor sebagai .CSV",
            command=lambda: self._proses_ekspor("csv"),
            **theme.style_tombol_sekunder()
        ).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        ctk.CTkLabel(
            kartu, text="Pratinjau Ringkasan:",
            font=theme.font_body(13, "bold"), text_color=theme.TEKS_UTAMA
        ).grid(row=4, column=0, sticky="w", padx=20, pady=(8, 4))

        self.label_pratinjau = ctk.CTkLabel(
            kartu, text="-", justify="left", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER
        )
        self.label_pratinjau.grid(row=5, column=0, sticky="w", padx=20, pady=(0, 20))

        self.entry_bulan_ekspor.bind("<Return>", lambda e: self._update_pratinjau())

        ctk.CTkButton(
            kartu, text="🔄 Perbarui Pratinjau",
            command=self._update_pratinjau,
            **theme.style_tombol_outline()
        ).grid(row=6, column=0, sticky="w", padx=20, pady=(0, 18))

    def _update_pratinjau(self):
        bulan = self.entry_bulan_ekspor.get().strip()
        if not bulan:
            self.label_pratinjau.configure(text="Masukkan bulan dengan format YYYY-MM.")
            return

        rekap = db.rekap_laba_rugi_bulan(bulan)
        teks = (
            f"Bulan          : {rekap['bulan']}\n"
            f"Pendapatan     : Rp {rekap['total_pendapatan']:,.0f}\n"
            f"Pengeluaran    : Rp {rekap['total_pengeluaran']:,.0f}\n"
            f"Gaji Karyawan  : Rp {rekap['total_gaji']:,.0f}\n"
            f"Laba Bersih    : Rp {rekap['laba_bersih']:,.0f}"
        )
        self.label_pratinjau.configure(text=teks)

    def _proses_ekspor(self, format_file):
        bulan = self.entry_bulan_ekspor.get().strip()
        if not bulan:
            messagebox.showwarning("MONIVA", "Masukkan bulan dengan format YYYY-MM terlebih dahulu.")
            return

        rekap = db.rekap_laba_rugi_bulan(bulan)

        ekstensi = "txt" if format_file == "txt" else "csv"
        path_simpan = filedialog.asksaveasfilename(
            title="Simpan Laporan Laba Rugi",
            defaultextension=f".{ekstensi}",
            initialfile=f"Laporan_LabaRugi_BaksoMaenyos_{bulan}.{ekstensi}",
            filetypes=[(f"File {ekstensi.upper()}", f"*.{ekstensi}")]
        )
        if not path_simpan:
            return

        try:
            if format_file == "txt":
                self._tulis_laporan_txt(path_simpan, rekap)
            else:
                self._tulis_laporan_csv(path_simpan, rekap)
        except OSError as e:
            messagebox.showerror("MONIVA", f"Gagal menyimpan file:\n{e}")
            return

        messagebox.showinfo("MONIVA", f"Laporan berhasil diekspor ke:\n{path_simpan}")
        self._update_pratinjau()

    def _tulis_laporan_txt(self, path, rekap):
        with open(path, "w", encoding="utf-8") as f:
            f.write("==========================================\n")
            f.write("   LAPORAN LABA RUGI - BAKSO MAENYOS\n")
            f.write(f"   Periode: {rekap['bulan']}\n")
            f.write("==========================================\n\n")
            f.write(f"Total Pendapatan (Setoran Terverifikasi) : Rp {rekap['total_pendapatan']:,.0f}\n")
            f.write(f"Total Pengeluaran Operasional             : Rp {rekap['total_pengeluaran']:,.0f}\n")
            f.write(f"Total Gaji Harian Karyawan                 : Rp {rekap['total_gaji']:,.0f}\n")
            f.write("------------------------------------------\n")
            f.write(f"LABA / RUGI BERSIH                         : Rp {rekap['laba_bersih']:,.0f}\n")
            f.write("==========================================\n")
            f.write("Dihasilkan otomatis oleh aplikasi MONIVA.\n")

    def _tulis_laporan_csv(self, path, rekap):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Laporan Laba Rugi - Bakso Maenyos"])
            writer.writerow(["Periode", rekap["bulan"]])
            writer.writerow([])
            writer.writerow(["Komponen", "Nominal (Rp)"])
            writer.writerow(["Total Pendapatan", f"{rekap['total_pendapatan']:.0f}"])
            writer.writerow(["Total Pengeluaran", f"{rekap['total_pengeluaran']:.0f}"])
            writer.writerow(["Total Gaji Karyawan", f"{rekap['total_gaji']:.0f}"])
            writer.writerow(["Laba/Rugi Bersih", f"{rekap['laba_bersih']:.0f}"])

    # ------------------------------------------------------------------
    def refresh_semua_data(self):
        """Dipanggil setiap ada perubahan data agar semua tab tetap sinkron."""
        self._refresh_dasbor()
        self._refresh_barang_bawaan()
        self._refresh_pengeluaran()
        self._update_pratinjau()
