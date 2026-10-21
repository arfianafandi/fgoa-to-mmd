#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FGO Arcade to MMD Converter - Graphical User Interface (GUI)
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import subprocess

TOOL_DIR = os.path.dirname(os.path.abspath(__file__))
if TOOL_DIR not in sys.path:
    sys.path.insert(0, TOOL_DIR)

import fgoa_to_mmd

class FGOAConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FGO Arcade to MMD Converter")
        self.root.geometry("780x560")
        self.root.minsize(650, 480)

        # Apply system styling
        self.style = ttk.Style()
        try:
            self.style.theme_use('vista')
        except Exception:
            pass

        self._build_ui()

    def _build_ui(self):
        # Header banner
        header_frame = ttk.Frame(self.root, padding="15 12 15 8")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(header_frame, text="FGO Arcade to MMD Model Converter", font=("Segoe UI", 16, "bold"))
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(header_frame, text="Otomatis memperbaiki tekstur, alfa transparansi, tulang hierarki, dan orientasi MMD.", font=("Segoe UI", 9))
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 0))

        # Main container
        main_frame = ttk.Frame(self.root, padding="15 5 15 15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Input Path section
        path_box = ttk.LabelFrame(main_frame, text="Target Input (Folder Model atau File .PMX)", padding="10")
        path_box.pack(fill=tk.X, pady=(0, 10))

        self.path_var = tk.StringVar(value=r"E:\FGO\FGOA")
        path_entry = ttk.Entry(path_box, textvariable=self.path_var, font=("Segoe UI", 10))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        btn_browse_folder = ttk.Button(path_box, text="Pilih Folder", command=self._browse_folder)
        btn_browse_folder.pack(side=tk.LEFT, padx=(0, 5))

        btn_browse_file = ttk.Button(path_box, text="Pilih .PMX", command=self._browse_file)
        btn_browse_file.pack(side=tk.LEFT)

        # Action Buttons frame
        act_frame = ttk.Frame(main_frame)
        act_frame.pack(fill=tk.X, pady=(0, 10))

        self.btn_convert = ttk.Button(act_frame, text="▶  Convert Target yang Dipilih", command=self._start_single_convert)
        self.btn_convert.pack(side=tk.LEFT, padx=(0, 8), ipady=3)

        self.btn_batch = ttk.Button(act_frame, text="⚡ Convert SEMUA di E:\\FGO\\FGOA", command=self._start_batch_convert)
        self.btn_batch.pack(side=tk.LEFT, padx=(0, 8), ipady=3)

        self.btn_open_folder = ttk.Button(act_frame, text="📁 Buka di Explorer", command=self._open_in_explorer)
        self.btn_open_folder.pack(side=tk.RIGHT, ipady=3)

        # Log Console section
        log_box = ttk.LabelFrame(main_frame, text="Log Proses Konversi", padding="8")
        log_box.pack(fill=tk.BOTH, expand=True)

        self.log_text = ScrolledText(log_box, wrap=tk.WORD, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="Siap. Silakan pilih folder atau file model untuk mulai konversi.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding="6 3")
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self._log("FGO Arcade to MMD Converter siap.")
        self._log("Anda bisa memilih folder model individu (misal: 'WP Saber') atau langsung convert semua model.")

    def _browse_folder(self):
        initial = self.path_var.get() if os.path.exists(self.path_var.get()) else r"E:\FGO\FGOA"
        selected = filedialog.askdirectory(initialdir=initial, title="Pilih Folder Model FGO Arcade")
        if selected:
            self.path_var.set(selected)

    def _browse_file(self):
        initial = self.path_var.get() if os.path.exists(self.path_var.get()) else r"E:\FGO\FGOA"
        if os.path.isfile(initial):
            initial = os.path.dirname(initial)
        selected = filedialog.filedialog.askopenfilename(
            initialdir=initial,
            title="Pilih File .PMX Model",
            filetypes=[("PMX Model", "*.pmx"), ("All files", "*.*")]
        )
        if selected:
            self.path_var.set(selected)

    def _open_in_explorer(self):
        p = self.path_var.get().strip()
        if not p or not os.path.exists(p):
            messagebox.showwarning("Peringatan", "Path tidak ditemukan di komputer!")
            return
        if os.path.isfile(p):
            p = os.path.dirname(p)
        os.startfile(p)

    def _log(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def _set_ui_busy(self, busy):
        state = tk.DISABLED if busy else tk.NORMAL
        self.btn_convert.config(state=state)
        self.btn_batch.config(state=state)

    def _start_single_convert(self):
        target = self.path_var.get().strip('\"\' ')
        if not target or not os.path.exists(target):
            messagebox.showerror("Error", f"Path tidak valid: {target}")
            return
        self._set_ui_busy(True)
        self.status_var.set(f"Sedang mengonversi: {os.path.basename(target)}...")
        self._log(f"\n=======================================================")
        self._log(f"Memulai konversi: {target}")
        self._log(f"=======================================================")

        def run():
            try:
                fgoa_to_mmd.process_target(target, log_func=self._thread_log)
                self.root.after(0, self._on_complete, "Konversi selesai dengan sukses!")
            except Exception as e:
                self.root.after(0, self._on_error, str(e))

        threading.Thread(target=run, daemon=True).start()

    def _start_batch_convert(self):
        confirm = messagebox.askyesno(
            "Konfirmasi Batch Convert",
            "Apakah Anda ingin memproses dan mengonversi SELURUH model di E:\\FGO\\FGOA secara otomatis?"
        )
        if not confirm:
            return

        self._set_ui_busy(True)
        self.status_var.set("Sedang melakukan batch convert untuk seluruh E:\\FGO\\FGOA...")
        self._log(f"\n=======================================================")
        self._log(f"Memulai BATCH CONVERT untuk seluruh E:\\FGO\\FGOA...")
        self._log(f"=======================================================")

        def run():
            try:
                fgoa_to_mmd.process_target(r"E:\FGO\FGOA", log_func=self._thread_log)
                self.root.after(0, self._on_complete, "Batch convert seluruh model selesai!")
            except Exception as e:
                self.root.after(0, self._on_error, str(e))

        threading.Thread(target=run, daemon=True).start()

    def _thread_log(self, text):
        self.root.after(0, self._log, text)

    def _on_complete(self, msg):
        self._set_ui_busy(False)
        self.status_var.set(msg)
        self._log(f"\n[✓] {msg}")
        messagebox.showinfo("Sukses", msg)

    def _on_error(self, err_msg):
        self._set_ui_busy(False)
        self.status_var.set(f"Terjadi kesalahan: {err_msg}")
        self._log(f"\n[✗] ERROR: {err_msg}")
        messagebox.showerror("Error Konversi", f"Terjadi kesalahan saat proses:\n{err_msg}")


def main():
    root = tk.Tk()
    app = FGOAConverterGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
