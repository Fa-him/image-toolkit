import sys, os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt

# Optional modern UI (ttkbootstrap)
USING_TTKBOOTSTRAP = False
try:
    import ttkbootstrap as tb
    from ttkbootstrap import ttk
    from ttkbootstrap.constants import PRIMARY, SUCCESS, INFO, WARNING, DANGER, SECONDARY
    USING_TTKBOOTSTRAP = True
except Exception:
    import tkinter.ttk as ttk
    PRIMARY = SUCCESS = INFO = WARNING = DANGER = SECONDARY = None

# Algorithms
from algorithms.negative import image_negative_exact
from algorithms.threshold import threshold_loop
from algorithms.smoothing import smooth_image   
from algorithms.sharpening import sharpen_image 
from algorithms.edges import laplacian_manual
from algorithms.histogram import render_histogram_image
from algorithms.log_gamma import log_transform_manual, gamma_transform_manual
from algorithms.resize import resize_nearest_manual

# Constants
APP_TITLE = "Image Processing Toolkit"
DEV_PHOTO_SIZE = 160
NAME_FONT = ("Segoe UI", 18, "bold")
ID_FONT   = ("Segoe UI", 14)
BTN_FONT  = ("Segoe UI", 13, "bold")
BTN_WIDTH = 18
BTN_PADX, BTN_PADY = 8, 10

def resource_path(rel_path: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_path)


class App(tk.Tk if not USING_TTKBOOTSTRAP else tb.Window):
    def __init__(self):
        # default theme: superhero; alt: darkly
        if USING_TTKBOOTSTRAP:
            super().__init__(themename="superhero")
        else:
            super().__init__()

        try:
            self.tk.call("tk", "scaling", 1.4)
        except Exception:
            pass

        self.title(APP_TITLE)
        self.geometry("1400x900")
        self.resizable(True, True)

        self.original_img_pil = None
        self.result_img_pil = None
        self.left_tk = None
        self.right_tk = None

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        if not USING_TTKBOOTSTRAP:
            try:
                style.theme_use("clam")
            except Exception:
                pass

        def apply_big_style(style_obj):
            style_obj.configure("TButton", font=BTN_FONT, padding=(10, 10))
            style_obj.configure("Big.TLabelframe.Label", font=("Segoe UI", 14, "bold"))
            style_obj.configure("Card.TFrame", relief="flat")

        apply_big_style(style)

        # Top bar
        top = ttk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, pady=10)

        ttk.Label(top, text=APP_TITLE, font=("Segoe UI", 26, "bold")).pack(side=tk.LEFT, padx=16)

        if USING_TTKBOOTSTRAP:
            theme_wrap = ttk.Frame(top)
            theme_wrap.pack(side=tk.LEFT, padx=12)
            ttk.Label(theme_wrap, text="Theme:", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=(0, 6))
            theme_options = ["superhero", "darkly"]
            theme_var = tk.StringVar(value="superhero")
            theme_box = ttk.Combobox(theme_wrap, textvariable=theme_var, values=theme_options, width=12, state="readonly")
            theme_box.pack(side=tk.LEFT)
            def on_theme_change(event=None):
                try:
                    self.style.theme_use(theme_var.get())
                    apply_big_style(self.style)
                except Exception as e:
                    messagebox.showerror("Theme", f"Failed to switch to theme '{theme_var.get()}'.\n{e}")
            theme_box.bind("<<ComboboxSelected>>", on_theme_change)
            apply_big_style(self.style)

        # Developer card
        dev = ttk.Frame(top)
        dev.pack(side=tk.RIGHT, padx=20)
        photo_path = resource_path("assets/Dev.png")
        try:
            img = Image.open(photo_path).resize((DEV_PHOTO_SIZE, DEV_PHOTO_SIZE), Image.LANCZOS)
            self.dev_photo_tk = ImageTk.PhotoImage(img)
            ttk.Label(dev, image=self.dev_photo_tk).grid(row=0, column=0, rowspan=2, padx=(0, 14))
        except Exception:
            ttk.Label(dev, text="[photo]", font=("Segoe UI", 14)).grid(row=0, column=0, rowspan=2, padx=(0, 14))
        ttk.Label(dev, text="Md Fahim Bin Alam", font=NAME_FONT).grid(row=0, column=1, sticky="w")
        ttk.Label(dev, text="ID: 0812220205101037", font=ID_FONT).grid(row=1, column=1, sticky="w")

        # Two toolbars
        bar1 = ttk.Frame(self); bar1.pack(side=tk.TOP, fill=tk.X, pady=(15, 5))
        bar2 = ttk.Frame(self); bar2.pack(side=tk.TOP, fill=tk.X, pady=(5, 15))

        def add_btn(parent, text, cmd, bootstyle=None):
            btn = ttk.Button(parent, text=text, command=cmd, width=BTN_WIDTH)
            if USING_TTKBOOTSTRAP and bootstyle:
                btn.configure(bootstyle=bootstyle)
            btn.pack(side=tk.LEFT, padx=BTN_PADX, pady=BTN_PADY)
            return btn

        add_btn(bar1, "Open Image", self.open_image, PRIMARY)
        add_btn(bar1, "Save Result As", self.save_result, SUCCESS)
        add_btn(bar1, "Negative", self.apply_negative_exact, INFO)
        add_btn(bar1, "Threshold", self.apply_threshold, INFO)
        add_btn(bar1, "Smoothing", self.apply_smoothing, INFO)   # choice + strength
        add_btn(bar1, "Sharpen", self.apply_sharpening, INFO)    # choice + strength

        add_btn(bar2, "Laplacian Edge", self.apply_laplacian, INFO)
        add_btn(bar2, "Histogram", self.apply_histogram_to_result, INFO)
        add_btn(bar2, "Log Transform", self.apply_log, WARNING)
        add_btn(bar2, "Gamma Transform", self.apply_gamma, WARNING)
        add_btn(bar2, "Resize", self.apply_resize, SECONDARY)
        add_btn(bar2, "Reset", self.reset_result, DANGER)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=6)

        # Center
        center = ttk.Frame(self); center.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)
        left_card = ttk.Frame(center, style="Card.TFrame")
        right_card = ttk.Frame(center, style="Card.TFrame")
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        right_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        ttk.Label(left_card, text="Original", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=12, pady=8)
        ttk.Label(right_card, text="Result", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=12, pady=8)

        self.left_canvas = tk.Label(left_card, bg="#1c1f26" if USING_TTKBOOTSTRAP else "#222",
                                    fg="white", text="Open an image…", font=("Segoe UI", 15))
        self.left_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        self.right_canvas = tk.Label(right_card, bg="#1c1f26" if USING_TTKBOOTSTRAP else "#222",
                                     fg="white", text="(no result yet)", font=("Segoe UI", 15))
        self.right_canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Status
        status_wrap = ttk.Frame(self); status_wrap.pack(side=tk.BOTTOM, fill=tk.X)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(status_wrap, textvariable=self.status, anchor="w", font=("Segoe UI", 12)).pack(
            side=tk.BOTTOM, fill=tk.X, padx=10, pady=6
        )

    # ---------- Small helpers ----------
    def _fit_preview(self, pil_img, max_w=600, max_h=600):
        w, h = pil_img.size
        scale = min(max_w / w, max_h / h, 1.0)
        return pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    def _pil_to_np(self, pil_img): return np.array(pil_img)
    def _np_to_pil(self, arr):    return Image.fromarray(arr.astype(np.uint8))

    def _refresh_canvases(self):
        if self.original_img_pil:
            left = self._fit_preview(self.original_img_pil)
            self.left_tk = ImageTk.PhotoImage(left)
            self.left_canvas.configure(image=self.left_tk, text="")
        else:
            self.left_canvas.configure(image="", text="Open an image…")

        if self.result_img_pil:
            right = self._fit_preview(self.result_img_pil)
            self.right_tk = ImageTk.PhotoImage(right)
            self.right_canvas.configure(image=self.right_tk, text="")
        else:
            self.right_canvas.configure(image="", text="(no result yet)")

    # ---------- Centering helper ----------
    def _center_on_parent(self, win, pad=(0, 0)):
        """Center a Toplevel `win` over the main application window."""
        win.update_idletasks()
        pw, ph = self.winfo_width(), self.winfo_height()
        px, py = self.winfo_rootx(), self.winfo_rooty()
        ww, wh = win.winfo_reqwidth(), win.winfo_reqheight()
        x = px + (pw - ww) // 2 + int(pad[0])
        y = py + (ph - wh) // 2 + int(pad[1])
        if x < 0: x = 0
        if y < 0: y = 0
        win.geometry(f"+{x}+{y}")

    # ---------- Choice dialogs ----------
    def _ask_choice(self, title, prompt, options, initial=0):
        """Modal radio-button choice dialog. Returns selected string or None."""
        win = tk.Toplevel(self)
        win.title(title)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        ttk.Label(win, text=prompt, font=("Segoe UI", 12, "bold")).pack(padx=12, pady=(12, 6), anchor="w")

        var = tk.IntVar(value=initial)
        for idx, label in enumerate(options):
            ttk.Radiobutton(win, text=label, variable=var, value=idx).pack(anchor="w", padx=16, pady=3)

        chosen = {"value": None}
        btnrow = ttk.Frame(win); btnrow.pack(fill=tk.X, padx=12, pady=12)
        def ok():
            chosen["value"] = options[var.get()]
            win.grab_release(); win.destroy()
        def cancel():
            chosen["value"] = None
            win.grab_release(); win.destroy()
        ttk.Button(btnrow, text="OK", width=12, command=ok).pack(side=tk.RIGHT, padx=6)
        ttk.Button(btnrow, text="Cancel", width=12, command=cancel).pack(side=tk.RIGHT, padx=6)

        # center the dialog over the main window
        self._center_on_parent(win)

        win.wait_window()
        return chosen["value"]

    # ---------- Source chooser ----------
    def _choose_source_array(self):
        if self.original_img_pil is None:
            messagebox.showinfo("No image", "Open an image first.")
            return None, None
        src_pil, src_label = self.original_img_pil, "Original"
        if self.result_img_pil is not None:
            use_result = messagebox.askyesno(
                "Apply To",
                "Apply to last RESULT instead of ORIGINAL?\n\nYes = Result (last output)\nNo  = Original (input)"
            )
            if use_result:
                src_pil, src_label = self.result_img_pil, "Result"
        return self._pil_to_np(src_pil), src_label

    # ---------- Progress (modal) ----------
    def _run_with_progress(self, title, worker_fn, callback_on_done):
        modal = tk.Toplevel(self)
        modal.title(title)
        modal.geometry("380x120")
        modal.resizable(False, False)
        modal.transient(self)
        modal.grab_set()

        ttk.Label(modal, text=title, font=("Segoe UI", 12, "bold")).pack(pady=(12, 6))
        pb = ttk.Progressbar(modal, mode="indeterminate", length=300)
        pb.pack(pady=8); pb.start(10)

        # center the modal after layout
        self._center_on_parent(modal)

        result_container = {"ok": False, "value": None, "error": None}
        def run():
            try:
                res = worker_fn()
                result_container["ok"] = True
                result_container["value"] = res
            except Exception as e:
                result_container["ok"] = False
                result_container["error"] = e
        t = threading.Thread(target=run, daemon=True); t.start()

        def poll():
            if t.is_alive():
                modal.after(100, poll)
            else:
                pb.stop(); modal.grab_release(); modal.destroy()
                if result_container["ok"]:
                    callback_on_done(result_container["value"])
                else:
                    messagebox.showerror("Operation failed", str(result_container["error"]))
        modal.after(150, poll)

    # ---------- Actions ----------
    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images","*.png;*.jpg;*.jpeg;*.bmp")])
        if not path: return
        try:
            img = Image.open(path)
            if img.mode not in ("L","RGB"): img = img.convert("RGB")
            self.original_img_pil, self.result_img_pil = img, None
            self._refresh_canvases()
            self.status.set(f"Opened: {path}")
        except Exception as e:
            messagebox.showerror("Open failed", str(e))

    def save_result(self):
        if not self.result_img_pil:
            messagebox.showinfo("No result","No processed image yet."); return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                filetypes=[("PNG","*.png"),("JPEG","*.jpg;*.jpeg"),("BMP","*.bmp")])
        if not path: return
        try:
            self.result_img_pil.save(path); self.status.set(f"Saved: {path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def reset_result(self):
        self.result_img_pil = None
        self._refresh_canvases()
        self.status.set("Reset to original")

    # Generic apply with source + progress
    def _apply_with_source(self, compute_func, label):
        src_arr, src_label = self._choose_source_array()
        if src_arr is None: return

        def worker(): return compute_func(src_arr)
        def on_done(out):
            if isinstance(out, Image.Image):
                self.result_img_pil = out
            else:
                self.result_img_pil = self._np_to_pil(out)
            self._refresh_canvases()
            self.status.set(f"Applied {label} (on {src_label})")

        self._run_with_progress(f"{label}…", worker, on_done)

    # Operations
    def apply_negative_exact(self):
        self._apply_with_source(lambda a: image_negative_exact(a, True), "Negative")

    def apply_threshold(self):
        if self.original_img_pil is None and self.result_img_pil is None:
            return messagebox.showinfo("No image", "Open an image first.")
        t = simpledialog.askinteger("Threshold", "Enter threshold (0–255):",
                                    minvalue=0, maxvalue=255, initialvalue=150)
        if t is None: return
        self._apply_with_source(lambda a: threshold_loop(a, t=int(t)), f"Threshold (t={t})")

    # ----- Smoothing with choices (Mean / Weighted / Gaussian + Low/Med/High) -----
    def apply_smoothing(self):
        filt = self._ask_choice(
            "Smoothing",
            "Choose smoothing filter:",
            ["Mean (3×3)", "Weighted (1-2-1)", "Gaussian (1-2-1)"],
            initial=1
        )
        if filt is None: return
        mode_map = {
            "Mean (3×3)": "mean",
            "Weighted (1-2-1)": "weighted",
            "Gaussian (1-2-1)": "gaussian",
        }
        mode = mode_map.get(filt, "mean")

        strength = self._ask_choice(
            "Strength",
            "Choose smoothing strength:",
            ["Low", "Medium", "High"],
            initial=1
        )
        if strength is None: return
        strength = strength.lower()

        self._apply_with_source(lambda a: smooth_image(a, mode=mode, strength=strength),
                                f"Smoothing - {filt} / {strength.capitalize()}")

    # ----- Sharpening with choices (First/Second order + Low/Med/High) -----
    def apply_sharpening(self):
        kind_label = self._ask_choice(
            "Sharpening",
            "Choose sharpening method:",
            ["First-order derivative", "Second-order derivative"],
            initial=1
        )
        if kind_label is None: return
        kind = "first" if "First" in kind_label else "second"

        strength = self._ask_choice(
            "Strength",
            "Choose sharpening strength:",
            ["Low", "Medium", "High"],
            initial=1
        )
        if strength is None: return
        strength = strength.lower()

        self._apply_with_source(lambda a: sharpen_image(a, kind=kind, strength=strength),
                                f"Sharpening - {kind_label} / {strength.capitalize()}")

    def apply_laplacian(self):
        self._apply_with_source(laplacian_manual, "Laplacian Edge")

    def apply_histogram_to_result(self):
        self._apply_with_source(lambda a: render_histogram_image(a, figsize=(8, 5)), "Histogram")

    def apply_log(self):
        self._apply_with_source(log_transform_manual, "Log Transform")

    def apply_gamma(self):
        if self.original_img_pil is None and self.result_img_pil is None:
            return messagebox.showinfo("No image","Open an image first.")
        g = simpledialog.askfloat("Gamma","Enter gamma (>0):",minvalue=0.01,maxvalue=20.0,initialvalue=2.2)
        if g is None: return
        self._apply_with_source(lambda a: gamma_transform_manual(a, g), f"Gamma Transform (γ={g:.3g})")

    def apply_resize(self):
        if self.original_img_pil is None and self.result_img_pil is None:
            return messagebox.showinfo("No image","Open an image first.")
        try:
            s = simpledialog.askstring("Resize","Enter width,height (e.g., 800,600)")
            if not s: return
            w, h = map(int, s.replace(" ", "").split(","))
            if w < 1 or h < 1 or w > 10000 or h > 10000: raise ValueError
        except Exception:
            return messagebox.showerror("Resize","Invalid size, e.g. 800,600")
        self._apply_with_source(lambda a: resize_nearest_manual(a, w, h), f"Resize {w}x{h}")


if __name__ == "__main__":
    App().mainloop()
