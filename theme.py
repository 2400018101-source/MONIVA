"""
theme.py
-------------------------------------------------------------------
Pusat konfigurasi tampilan (warna, font, ukuran) untuk seluruh
aplikasi MONIVA. Dengan memusatkan nilai-nilai ini di satu file,
seluruh halaman GUI memiliki nuansa visual yang konsisten:
hangat, energik, dan premium — sesuai identitas bisnis kuliner
"Bakso Maenyos".
-------------------------------------------------------------------
"""

#import customtkinter as ctk

# =====================================================================
# PALET WARNA UTAMA
# =====================================================================
# Merah & Oranye sebagai warna identitas kuliner, dipadukan dengan
# latar gelap agar warna-warna tersebut tampak kontras dan premium.

MERAH_TUA = "#B71C1C"       # Merah gelap - untuk header, elemen penting
MERAH = "#D32F2F"           # Merah utama - tombol primer, aksen
MERAH_HOVER = "#E53935"     # Merah lebih terang - efek hover

ORANYE_TUA = "#F57C00"      # Oranye gelap - aksen sekunder
ORANYE = "#FF9800"          # Oranye utama - highlight, badge, grafik
ORANYE_HOVER = "#FFA726"    # Oranye lebih terang - efek hover

# Latar & permukaan (dark mode custom, bukan hitam pekat agar lebih lembut di mata)
BG_UTAMA = "#1A1410"        # Latar utama aplikasi (coklat-hitam hangat)
BG_SIDEBAR = "#241A14"      # Latar sidebar/navigasi
BG_KARTU = "#2B2019"        # Latar kartu/panel konten
BG_INPUT = "#352720"        # Latar input field

# Teks
TEKS_UTAMA = "#FFF3E0"      # Putih krem hangat - teks utama
TEKS_SEKUNDER = "#D7CCC8"   # Abu kecoklatan - teks sekunder/label
TEKS_MUTED = "#A1887F"      # Abu lebih redup - placeholder/hint

# Status
HIJAU_SUKSES = "#43A047"    # Status Verified / sukses
KUNING_PENDING = "#FBC02D"  # Status Pending / menunggu
MERAH_GAGAL = "#E53935"     # Status error / gagal

# =====================================================================
# FONT
# =====================================================================
FONT_KELUARGA = "Segoe UI"  # Fallback otomatis ke font sistem modern

def font_judul(size=24, weight="bold"):
    return ctk.CTkFont(family=FONT_KELUARGA, size=size, weight=weight)

def font_subjudul(size=16, weight="bold"):
    return ctk.CTkFont(family=FONT_KELUARGA, size=size, weight=weight)

def font_body(size=13, weight="normal"):
    return ctk.CTkFont(family=FONT_KELUARGA, size=size, weight=weight)

def font_kecil(size=11, weight="normal"):
    return ctk.CTkFont(family=FONT_KELUARGA, size=size, weight=weight)


# =====================================================================
# KONSTANTA STYLING UMUM
# =====================================================================
RADIUS_TOMBOL = 8       # Sesuai spesifikasi: sudut membulat corner_radius=8
RADIUS_KARTU = 12
TINGGI_TOMBOL = 40
TINGGI_INPUT = 40


def setup_tema_aplikasi():
    """Mengatur mode tampilan global CustomTkinter (dipanggil sekali di main.py)."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")  # basis tema, warna komponen di-override manual


def style_tombol_primer():
    """Dict style siap pakai untuk tombol aksi utama (merah)."""
    return dict(
        corner_radius=RADIUS_TOMBOL,
        height=TINGGI_TOMBOL,
        fg_color=MERAH,
        hover_color=MERAH_HOVER,
        text_color=TEKS_UTAMA,
        font=font_body(14, "bold"),
    )


def style_tombol_sekunder():
    """Dict style siap pakai untuk tombol aksi sekunder (oranye)."""
    return dict(
        corner_radius=RADIUS_TOMBOL,
        height=TINGGI_TOMBOL,
        fg_color=ORANYE_TUA,
        hover_color=ORANYE_HOVER,
        text_color="#1A1410",
        font=font_body(14, "bold"),
    )


def style_tombol_outline():
    """Dict style untuk tombol aksi netral/batal (garis tepi saja)."""
    return dict(
        corner_radius=RADIUS_TOMBOL,
        height=TINGGI_TOMBOL,
        fg_color="transparent",
        hover_color=BG_INPUT,
        border_width=1,
        border_color=TEKS_MUTED,
        text_color=TEKS_SEKUNDER,
        font=font_body(13),
    )


def style_input():
    """Dict style siap pakai untuk CTkEntry/CTkComboBox."""
    return dict(
        corner_radius=RADIUS_TOMBOL,
        height=TINGGI_INPUT,
        fg_color=BG_INPUT,
        border_color=ORANYE_TUA,
        text_color=TEKS_UTAMA,
        font=font_body(13),
    )


# =====================================================================
# KOMPONEN: INPUT PASSWORD DENGAN TOGGLE LIHAT/SEMBUNYIKAN (IKON MATA)
# =====================================================================
class PasswordEntry(ctk.CTkFrame):
    """
    Komponen reusable: field password disertai tombol ikon mata (👁 / 🙈)
    di sisi kanan untuk menampilkan atau menyembunyikan teks password.

    Dipakai di halaman Login, form Lupa Password, dan form Ganti Password
    agar perilakunya konsisten di seluruh aplikasi.

    Cara pakai (mirip CTkEntry biasa):
        pw = PasswordEntry(parent, placeholder_text="Masukkan password")
        pw.grid(...)
        nilai = pw.get()
        pw.bind_enter(fungsi_callback)   # opsional, untuk tombol Enter
    """

    def __init__(self, master, placeholder_text="", width=320, **kwargs):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        self._terlihat = False  # status password: tersembunyi secara default

        style = style_input()
        style.update(kwargs)  # memungkinkan override style jika diperlukan

        self.entry = ctk.CTkEntry(
            self, placeholder_text=placeholder_text, show="•",
            width=width, **style
        )
        self.entry.grid(row=0, column=0, sticky="ew")

        # Tombol ikon mata: bulat kecil, menempel tepat di sisi kanan entry
        self.btn_toggle = ctk.CTkButton(
            self, text="👁", width=36, height=TINGGI_INPUT,
            corner_radius=RADIUS_TOMBOL,
            fg_color=BG_INPUT, hover_color=ORANYE_TUA,
            text_color=TEKS_MUTED, font=font_body(14),
            command=self._toggle_visibilitas,
        )
        self.btn_toggle.grid(row=0, column=1, padx=(6, 0))

    def _toggle_visibilitas(self):
        """Membalik status tampil/sembunyi teks password setiap tombol diklik."""
        self._terlihat = not self._terlihat
        if self._terlihat:
            self.entry.configure(show="")       # tampilkan teks asli
            self.btn_toggle.configure(text="🙈", text_color=ORANYE)
        else:
            self.entry.configure(show="•")       # sembunyikan lagi (default aman)
            self.btn_toggle.configure(text="👁", text_color=TEKS_MUTED)

    # --- Method pass-through agar pemakaian mirip CTkEntry biasa -----------
    def get(self):
        return self.entry.get()

    def delete(self, first, last=None):
        self.entry.delete(first, last)

    def insert(self, index, text):
        self.entry.insert(index, text)

    def bind_enter(self, callback):
        """Memicu callback saat tombol Enter ditekan di dalam field password."""
        self.entry.bind("<Return>", lambda e: callback())

    def focus(self):
        self.entry.focus()
