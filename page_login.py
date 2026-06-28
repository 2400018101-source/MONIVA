"""
page_login.py
-------------------------------------------------------------------
Halaman Login MONIVA.

Form bersih di tengah layar untuk memasukkan username & password.
Setelah login berhasil, aplikasi akan memanggil callback
`on_login_success(user_row)` yang diteruskan dari main.py, lalu
main.py yang akan memutuskan untuk menampilkan Dashboard Karyawan
atau Dashboard Pemilik berdasarkan kolom `role`.

Juga berisi `LupaPasswordDialog`: jendela modal 2 langkah untuk
mereset password lewat pertanyaan keamanan (tanpa perlu email/SMS,
karena aplikasi berjalan offline/lokal).
-------------------------------------------------------------------
"""

import customtkinter as ctk
from tkinter import messagebox

import database as db
import theme


class LoginFrame(ctk.CTkFrame):
    """Frame berisi seluruh elemen visual halaman login."""

    def __init__(self, master, on_login_success):
        super().__init__(master, fg_color=theme.BG_UTAMA)
        self.on_login_success = on_login_success
        self._build_ui()

    def _build_ui(self):
        # Kartu login diletakkan di tengah memakai grid agar responsif
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        kartu = ctk.CTkFrame(
            self,
            fg_color=theme.BG_KARTU,
            corner_radius=theme.RADIUS_KARTU,
            width=400,
            height=640,
            border_width=1,
            border_color=theme.MERAH_TUA,
        )
        kartu.grid(row=0, column=0)
        kartu.grid_propagate(False)
        kartu.grid_columnconfigure(0, weight=1)

        # --- Logo / Judul Aplikasi ---------------------------------
        ctk.CTkLabel(
            kartu, text="🍜", font=ctk.CTkFont(size=42)
        ).grid(row=0, column=0, pady=(36, 0))

        ctk.CTkLabel(
            kartu, text="MONIVA",
            font=theme.font_judul(30, "bold"),
            text_color=theme.MERAH,
        ).grid(row=1, column=0, pady=(4, 0))

        ctk.CTkLabel(
            kartu, text="Monitor & Visualisasi Keuangan",
            font=theme.font_kecil(12),
            text_color=theme.TEKS_MUTED,
        ).grid(row=2, column=0, pady=(0, 4))

        ctk.CTkLabel(
            kartu, text="Bakso Maenyos",
            font=theme.font_subjudul(15, "bold"),
            text_color=theme.ORANYE,
        ).grid(row=3, column=0, pady=(0, 20))

        # --- Input Username ------------------------------------------
        ctk.CTkLabel(
            kartu, text="Username", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=4, column=0, sticky="w", padx=40)

        self.entry_username = ctk.CTkEntry(
            kartu, placeholder_text="Masukkan username",
            width=320, **theme.style_input()
        )
        self.entry_username.grid(row=5, column=0, pady=(4, 14), padx=40)

        # --- Input Password (dengan toggle ikon mata) -------------------
        ctk.CTkLabel(
            kartu, text="Password", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=6, column=0, sticky="w", padx=40)

        self.entry_password = theme.PasswordEntry(
            kartu, placeholder_text="Masukkan password", width=276
        )
        self.entry_password.grid(row=7, column=0, pady=(4, 4), padx=40, sticky="ew")
        # Tekan Enter di password langsung memicu login
        self.entry_password.bind_enter(self._proses_login)

        # --- Link "Lupa Password?" ------------------------------------
        link_lupa = ctk.CTkLabel(
            kartu, text="Lupa password?", anchor="e",
            font=theme.font_kecil(11, "bold"), text_color=theme.ORANYE,
            cursor="hand2",
        )
        link_lupa.grid(row=8, column=0, sticky="e", padx=40, pady=(0, 8))
        link_lupa.bind("<Button-1>", lambda e: self._buka_lupa_password())

        # --- Label info / error --------------------------------------
        self.label_info = ctk.CTkLabel(
            kartu, text="", font=theme.font_kecil(12), text_color=theme.MERAH_GAGAL,
            wraplength=320,
        )
        self.label_info.grid(row=9, column=0, pady=(0, 4))

        # --- Tombol Login ----------------------------------------------
        ctk.CTkButton(
            kartu, text="Masuk", width=320,
            command=self._proses_login,
            **theme.style_tombol_primer()
        ).grid(row=10, column=0, pady=(8, 16), padx=40)

        # --- Hint info akun (kredensial lengkap ada di README) -------------
        hint = ctk.CTkFrame(kartu, fg_color=theme.BG_INPUT, corner_radius=8)
        hint.grid(row=11, column=0, pady=(4, 0), padx=40, sticky="ew")
        ctk.CTkLabel(
            hint,
            text="Daftar username & password Pemilik/Karyawan ada di README.md",
            font=theme.font_kecil(11), text_color=theme.TEKS_MUTED,
            justify="left", wraplength=300,
        ).pack(padx=12, pady=8)

    def _proses_login(self):
        """Validasi input lalu cek ke database. Tampilkan pesan error jika gagal."""
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            self.label_info.configure(text="Username dan password wajib diisi.")
            return

        user = db.verifikasi_login(username, password)
        if user is None:
            self.label_info.configure(text="Username atau password salah.")
            return

        self.label_info.configure(text="")
        self.on_login_success(user)

    def _buka_lupa_password(self):
        """Membuka jendela modal Lupa Password, mengisi username jika sudah diketik."""
        LupaPasswordDialog(self, username_awal=self.entry_username.get().strip())


class LupaPasswordDialog(ctk.CTkToplevel):
    """
    Jendela modal 2 langkah untuk reset password lewat pertanyaan keamanan:
      Langkah 1 - pengguna mengetik username, sistem menampilkan pertanyaan
                  keamanan miliknya, lalu pengguna menjawabnya.
      Langkah 2 - jika jawaban benar, pengguna mengetik password baru
                  (2x, dengan toggle mata) lalu disimpan ke database.
    """

    def __init__(self, master, username_awal=""):
        super().__init__(master)
        self.title("Lupa Password - MONIVA")
        self.geometry("380x420")
        self.resizable(False, False)
        self.configure(fg_color=theme.BG_KARTU)

        self.username_valid = None      # diisi setelah langkah 1 berhasil
        self._jawaban_benar_cache = ""  # jawaban yang sudah lolos verifikasi

        # Modal: kunci interaksi ke jendela utama selagi dialog ini terbuka
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self._tampilkan_langkah_1(username_awal)

    # ------------------------------------------------------------------
    def _bersihkan_frame(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ------------------------------------------------------------------
    # LANGKAH 1: Username + Pertanyaan Keamanan
    # ------------------------------------------------------------------
    def _tampilkan_langkah_1(self, username_awal=""):
        self._bersihkan_frame()

        ctk.CTkLabel(
            self, text="🔑 Lupa Password",
            font=theme.font_subjudul(17, "bold"), text_color=theme.MERAH
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            self, text="Masukkan username Anda untuk melihat pertanyaan keamanan.",
            font=theme.font_kecil(11), text_color=theme.TEKS_MUTED,
            wraplength=320, justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 12))

        ctk.CTkLabel(
            self, text="Username", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=2, column=0, sticky="w", padx=24)

        self.entry_username = ctk.CTkEntry(self, width=320, **theme.style_input())
        self.entry_username.grid(row=3, column=0, padx=24, pady=(4, 10))
        if username_awal:
            self.entry_username.insert(0, username_awal)

        ctk.CTkButton(
            self, text="Tampilkan Pertanyaan Keamanan", width=320,
            command=self._proses_cek_username,
            **theme.style_tombol_sekunder()
        ).grid(row=4, column=0, padx=24, pady=(4, 4))

        self.label_status_1 = ctk.CTkLabel(
            self, text="", font=theme.font_kecil(11), text_color=theme.MERAH_GAGAL,
            wraplength=320,
        )
        self.label_status_1.grid(row=5, column=0, padx=24, pady=(4, 4))

        # --- Area pertanyaan & jawaban keamanan (muncul setelah username valid) ---
        self.frame_pertanyaan = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_pertanyaan.grid(row=6, column=0, sticky="ew", padx=24)
        self.frame_pertanyaan.grid_columnconfigure(0, weight=1)

    def _proses_cek_username(self):
        """Mengecek apakah username ada & punya pertanyaan keamanan, lalu menampilkannya."""
        username = self.entry_username.get().strip()
        if not username:
            self.label_status_1.configure(text="Username wajib diisi.")
            return

        pertanyaan = db.ambil_pertanyaan_keamanan(username)
        if pertanyaan is None:
            self.label_status_1.configure(text="Username tidak ditemukan.")
            return
        if not pertanyaan:
            self.label_status_1.configure(
                text="Akun ini belum memiliki pertanyaan keamanan. "
                     "Hubungi Pemilik untuk reset manual."
            )
            return

        self.label_status_1.configure(text="")
        self._username_tervalidasi = username
        self._tampilkan_form_jawaban(pertanyaan)

    def _tampilkan_form_jawaban(self, pertanyaan):
        """Menampilkan pertanyaan keamanan + field jawaban, di bawah tombol cek username."""
        for widget in self.frame_pertanyaan.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.frame_pertanyaan, text=f"❓ {pertanyaan}", anchor="w",
            font=theme.font_body(12, "bold"), text_color=theme.ORANYE,
            wraplength=320, justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(8, 6))

        self.entry_jawaban = ctk.CTkEntry(
            self.frame_pertanyaan, placeholder_text="Jawaban Anda",
            width=320, **theme.style_input()
        )
        self.entry_jawaban.grid(row=1, column=0, pady=(0, 10))
        self.entry_jawaban.bind("<Return>", lambda e: self._proses_verifikasi_jawaban())

        ctk.CTkButton(
            self.frame_pertanyaan, text="Verifikasi Jawaban", width=320,
            command=self._proses_verifikasi_jawaban,
            **theme.style_tombol_primer()
        ).grid(row=2, column=0)

    def _proses_verifikasi_jawaban(self):
        jawaban = self.entry_jawaban.get().strip()
        if not jawaban:
            self.label_status_1.configure(text="Jawaban tidak boleh kosong.")
            return

        if not db.verifikasi_jawaban_keamanan(self._username_tervalidasi, jawaban):
            self.label_status_1.configure(text="Jawaban keamanan salah. Coba lagi.")
            return

        self.username_valid = self._username_tervalidasi
        self._jawaban_benar_cache = jawaban  # disimpan untuk dipakai di langkah 2
        self._tampilkan_langkah_2()

    # ------------------------------------------------------------------
    # LANGKAH 2: Input Password Baru
    # ------------------------------------------------------------------
    def _tampilkan_langkah_2(self):
        self._bersihkan_frame()

        ctk.CTkLabel(
            self, text="✅ Verifikasi Berhasil",
            font=theme.font_subjudul(17, "bold"), text_color=theme.HIJAU_SUKSES
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 4))

        ctk.CTkLabel(
            self, text=f"Buat password baru untuk akun '{self.username_valid}'.",
            font=theme.font_kecil(11), text_color=theme.TEKS_MUTED,
            wraplength=320, justify="left",
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 14))

        ctk.CTkLabel(
            self, text="Password Baru", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=2, column=0, sticky="w", padx=24)

        self.entry_pw_baru = theme.PasswordEntry(self, placeholder_text="Minimal 6 karakter", width=276)
        self.entry_pw_baru.grid(row=3, column=0, padx=24, pady=(4, 10), sticky="ew")

        ctk.CTkLabel(
            self, text="Ulangi Password Baru", anchor="w",
            font=theme.font_body(12), text_color=theme.TEKS_SEKUNDER,
        ).grid(row=4, column=0, sticky="w", padx=24)

        self.entry_pw_konfirmasi = theme.PasswordEntry(self, placeholder_text="Ulangi password", width=276)
        self.entry_pw_konfirmasi.grid(row=5, column=0, padx=24, pady=(4, 10), sticky="ew")
        self.entry_pw_konfirmasi.bind_enter(self._proses_simpan_password_baru)

        self.label_status_2 = ctk.CTkLabel(
            self, text="", font=theme.font_kecil(11), text_color=theme.MERAH_GAGAL,
            wraplength=320,
        )
        self.label_status_2.grid(row=6, column=0, padx=24, pady=(0, 4))

        ctk.CTkButton(
            self, text="Simpan Password Baru", width=320,
            command=self._proses_simpan_password_baru,
            **theme.style_tombol_primer()
        ).grid(row=7, column=0, padx=24, pady=(4, 16))

    def _proses_simpan_password_baru(self):
        pw_baru = self.entry_pw_baru.get().strip()
        pw_konfirmasi = self.entry_pw_konfirmasi.get().strip()

        if not pw_baru or not pw_konfirmasi:
            self.label_status_2.configure(text="Kedua field password wajib diisi.")
            return
        if len(pw_baru) < 6:
            self.label_status_2.configure(text="Password baru minimal 6 karakter.")
            return
        if pw_baru != pw_konfirmasi:
            self.label_status_2.configure(text="Konfirmasi password tidak cocok.")
            return

        # Jawaban keamanan sudah divalidasi di langkah 1 dan disimpan di cache,
        # sehingga pengguna tidak perlu mengetik ulang jawabannya di langkah ini.
        sukses = db.reset_password_via_keamanan(
            self.username_valid, self._jawaban_benar_cache, pw_baru
        )
        if not sukses:
            self.label_status_2.configure(text="Terjadi kesalahan, silakan ulangi dari awal.")
            return

        messagebox.showinfo(
            "MONIVA", "Password berhasil diperbarui. Silakan login dengan password baru."
        )
        self.destroy()
