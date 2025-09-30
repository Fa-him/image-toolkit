# algorithms/histogram.py
import io
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")  # render off-screen
import matplotlib.pyplot as plt

def compute_histogram_manual(img_np: np.ndarray):
    
    if img_np.ndim == 2:
        H, W = img_np.shape
        hist = np.zeros(256, dtype=np.int64)
        for i in range(H):
            for j in range(W):
                v = int(img_np[i, j])
                hist[v] += 1
        return {"mode": "gray", "gray": hist}

    # color (assume 3 channels)
    H, W, C = img_np.shape
    assert C == 3, "Only 3-channel color supported"
    r_hist = np.zeros(256, dtype=np.int64)
    g_hist = np.zeros(256, dtype=np.int64)
    b_hist = np.zeros(256, dtype=np.int64)

    for i in range(H):
        for j in range(W):
            r = int(img_np[i, j, 0])
            g = int(img_np[i, j, 1])
            b = int(img_np[i, j, 2])
            r_hist[r] += 1
            g_hist[g] += 1
            b_hist[b] += 1

    return {"mode": "color", "r": r_hist, "g": g_hist, "b": b_hist}

def render_histogram_image(img_np: np.ndarray, figsize=(8, 5)) -> Image.Image:
    
    h = compute_histogram_manual(img_np)

    fig = plt.figure(figsize=figsize, dpi=120)
    ax = fig.add_subplot(111)
    ax.set_xlabel("Intensity (0–255)")
    ax.set_ylabel("Count")
    ax.grid(True, linestyle="--", linewidth=0.5)

    if h["mode"] == "gray":
        ax.set_title("Histogram (Grayscale)")
        ax.plot(range(256), h["gray"])
    else:
        ax.set_title("Histogram (Color)")
        ax.plot(range(256), h["r"], label="R")
        ax.plot(range(256), h["g"], label="G")
        ax.plot(range(256), h["b"], label="B")
        ax.legend()

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)

    hist_pil = Image.open(buf).convert("RGB")
    buf.close()
    return hist_pil
