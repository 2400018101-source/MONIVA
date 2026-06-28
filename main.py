"""
main.py
-------------------------------------------------------------------
Entry point aplikasi MONIVA (Monitor and Visualisasi) untuk
UMKM kuliner "Bakso Maenyos".

Menjalankan:
1. Inisialisasi database (buat tabel + data dummy jika belum ada).
2. Jendela utama CustomTkinter.
3. Navigasi antar-halaman: Login -> Dashboard Karyawan / Dashboard
   Pemilik (Role-Based Access Control) -> kembali ke Login (logout).

Cara menjalankan:
    pip install customtkinter matplotlib
    python main.py

Akun (data dummy otomatis tersedia di database, lihat database.py / README.md):
    Pemilik  -> username & password adalah PLACEHOLDER, harus diganti
                (lihat konstanta seed di database.py)
    Karyawan -> 5 akun unik (budi_karyawan, siti_staff, joko_kasir,
                rina_staff, agus_karyawan), lihat README.md untuk passwordnya
-------------------------------------------------------------------
"""

import customtkinter as ctk

import database as db
import theme
from page_login import LoginFrame
from page_karyawan import KaryawanFrame
from page_pemilik import PemilikFrame


class MonivaApp(ctk.CTk):
    """Jendela utama aplikasi yang mengatur perpindahan antar frame/halaman."""

    def __init__(self):
        super().__init__()

        self.title("MONIVA - Monitor & Visualisasi Keuangan | Bakso Maenyos")
        self.geometry("1180x720")
        self.minsize(1000, 640)
        self.configure(fg_color=theme.BG_UTAMA)

        # Frame yang sedang aktif (Login / Karyawan / Pemilik) disimpan
        # agar bisa dihapus bersih saat berpindah halaman.
        self.frame_aktif = None

        self.tampilkan_login()

    # ------------------------------------------------------------------
    def _ganti_frame(self, frame_baru):
        """Membersihkan frame lama lalu menampilkan frame baru secara penuh."""
        if self.frame_aktif is not None:
            self.frame_aktif.destroy()
        self.frame_aktif = frame_baru
        self.frame_aktif.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    def tampilkan_login(self):
        frame = LoginFrame(self, on_login_success=self._handle_login_success)
        self._ganti_frame(frame)

    def _handle_login_success(self, user_row):
        """
        Dipanggil oleh LoginFrame setelah kredensial valid.
        Mengarahkan ke dashboard yang sesuai berdasarkan kolom 'role'
        (inti dari Role-Based Access Control / RBAC pada MONIVA).
        """
        if user_row["role"] == "Pemilik":
            frame = PemilikFrame(self, user_row=user_row, on_logout=self.tampilkan_login)
        else:  # role == 'Karyawan'
            frame = KaryawanFrame(self, user_row=user_row, on_logout=self.tampilkan_login)
        self._ganti_frame(frame)


def main():
    # 1. Siapkan tema visual global (dark mode + font)
    theme.setup_tema_aplikasi()

    # 2. Pastikan database & tabel-tabelnya sudah ada, lengkap dengan data dummy
    db.init_db()

    # 3. Jalankan aplikasi
    app = MonivaApp()
    app.mainloop()


if __name__ == "__main__":
    main()
