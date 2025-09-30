# algorithms/threshold.py
import numpy as np

def _to_gray(rgb: np.ndarray) -> np.ndarray:
    if rgb.ndim == 2:
        return rgb.astype(np.uint8)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    return (0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)

def threshold_loop(img_np: np.ndarray, t: int = 150) -> np.ndarray:
    gray = _to_gray(img_np)
    h, w = gray.shape
    out = gray.copy()

    for i in range(h):
        for j in range(w):
            out[i, j] = 0 if out[i, j] < t else 255

    # replicate to RGB for the GUI
    out3 = np.stack([out, out, out], axis=2).astype(np.uint8)
    return out3
