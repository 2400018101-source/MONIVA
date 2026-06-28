"""
dialog_ganti_password.py
-------------------------------------------------------------------
Dialog modal "Ganti Password", dipakai bersama oleh Dashboard
Karyawan maupun Dashboard Pemilik (akses RBAC tidak relevan di sini
karena setiap pengguna yang login hanya bisa mengganti password
miliknya sendiri).

Mewajibkan pengguna mengetik password lama dengan benar sebelum
password baru disimpan, sebagai langkah verifikasi keamanan dasar.
Semua field password memakai komponen theme.PasswordEntry sehingga
ada toggle ikon mata (👁 / 🙈) untuk menampilkan/menyembunyikan teks.
-------------------------------------------------------------------
"""

import customtkinter as ctk
from tkinter import messagebox

import database as db
import theme


class GantiPasswordDialog(ctk.CTkToplevel):
    """Jendela modal untuk mengganti password milik user yang sedang login."""

    def __init__(self, master, user_row):
        super().__init__(master)
        self.user = user_row

        self.title("Ganti Password - MONIVA")
        self.geometry("380x430")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG_KARTU)

        # Modal: kunci interaksi ke jendela utama selagi dialog ini terbuka
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(
            self, text="🔒 Ganti Password",
            font=theme.font_subjudul(17, "bold"), text_color=theme.MERAH
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            self, text=f"Mengganti password untuk akun '{self.user['username']}'.",
            font=theme.font_kecil(11), text_color=theme.TEKS_MUTED,
            wraplength=320, justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 14))

        # --- Password lama ---------------------------------------------
        ctk.CTkLabel(
            self, text="Password Lama", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=2, column=0, sticky="w", padx=24)

        self.entry_pw_lama = theme.PasswordEntry(self, placeholder_text="Password saat ini", width=276)
        self.entry_pw_lama.grid(row=3, column=0, padx=24, pady=(4, 10), sticky="ew")

        # --- Password baru ---------------------------------------------
        ctk.CTkLabel(
            self, text="Password Baru", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=4, column=0, sticky="w", padx=24)

        self.entry_pw_baru = theme.PasswordEntry(self, placeholder_text="Minimal 6 karakter", width=276)
        self.entry_pw_baru.grid(row=5, column=0, padx=24, pady=(4, 10), sticky="ew")

        # --- Konfirmasi password baru -------------------------------------
        ctk.CTkLabel(
            self, text="Ulangi Password Baru", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=6, column=0, sticky="w", padx=24)

        self.entry_pw_konfirmasi = theme.PasswordEntry(self, placeholder_text="Ulangi password baru", width=276)
        self.entry_pw_konfirmasi.grid(row=7, column=0, padx=24, pady=(4, 10), sticky="ew")
        self.entry_pw_konfirmasi.bind_enter(self._proses_simpan)

        self.label_status = ctk.CTkLabel(
            self, text="", font=theme.font_kecil(11), text_color=theme.MERAH_GAGAL,
            wraplength=320,
        )
        self.label_status.grid(row=8, column=0, padx=24, pady=(0, 4))

        ctk.CTkButton(
            self, text="Simpan Password Baru", width=320,
            command=self._proses_simpan,
            **theme.style_tombol_primer()
        ).grid(row=9, column=0, padx=24, pady=(4, 16))

    def _proses_simpan(self):
        pw_lama = self.entry_pw_lama.get().strip()
        pw_baru = self.entry_pw_baru.get().strip()
        pw_konfirmasi = self.entry_pw_konfirmasi.get().strip()

        if not pw_lama or not pw_baru or not pw_konfirmasi:
            self.label_status.configure(text="Semua field wajib diisi.")
            return
        if len(pw_baru) < 6:
            self.label_status.configure(text="Password baru minimal 6 karakter.")
            return
        if pw_baru != pw_konfirmasi:
            self.label_status.configure(text="Konfirmasi password baru tidak cocok.")
            return
        if pw_baru == pw_lama:
            self.label_status.configure(text="Password baru tidak boleh sama dengan password lama.")
            return

        sukses = db.ubah_password(self.user["id_user"], pw_lama, pw_baru)
        if not sukses:
            self.label_status.configure(text="Password lama yang Anda masukkan salah.")
            return

        messagebox.showinfo("MONIVA", "Password berhasil diperbarui.")
        self.destroy()
