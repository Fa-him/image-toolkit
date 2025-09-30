# algorithms/log_gamma.py
import numpy as np

def log_transform_manual(img_np: np.ndarray) -> np.ndarray:
    
    if img_np.ndim == 2:
        src = img_np.astype(np.float32)
        max_v = float(src.max()) if src.size else 255.0
        c = 255.0 / np.log1p(max_v if max_v > 0 else 255.0)

        H, W = src.shape
        out = np.empty((H, W), dtype=np.uint8)
        for i in range(H):
            for j in range(W):
                s = c * np.log1p(src[i, j])
                if s < 0: s = 0
                elif s > 255: s = 255
                out[i, j] = int(round(s))
        return out

    a = img_np.astype(np.float32)
    H, W, C = a.shape
    out = np.empty((H, W, C), dtype=np.uint8)

    maxs = a.reshape(-1, C).max(axis=0)
    cs = np.empty(3, dtype=np.float32)
    for ch in range(C):
        m = float(maxs[ch]) if maxs[ch] > 0 else 255.0
        cs[ch] = 255.0 / np.log1p(m)

    for ch in range(C):
        for i in range(H):
            for j in range(W):
                s = cs[ch] * np.log1p(a[i, j, ch])
                if s < 0: s = 0
                elif s > 255: s = 255
                out[i, j, ch] = int(round(s))
    return out

def gamma_transform_manual(img_np: np.ndarray, gamma: float = 2.2) -> np.ndarray:
    
    if gamma <= 0:
        gamma = 1.0
    inv = 1.0 / gamma

    if img_np.ndim == 2:
        src = img_np.astype(np.float32)
        H, W = src.shape
        out = np.empty((H, W), dtype=np.uint8)
        for i in range(H):
            for j in range(W):
                s = 255.0 * ((src[i, j] / 255.0) ** inv)
                if s < 0: s = 0
                elif s > 255: s = 255
                out[i, j] = int(round(s))
        return out

    a = img_np.astype(np.float32)
    H, W, C = a.shape
    out = np.empty((H, W, C), dtype=np.uint8)

    for ch in range(C):
        for i in range(H):
            for j in range(W):
                s = 255.0 * ((a[i, j, ch] / 255.0) ** inv)
                if s < 0: s = 0
                elif s > 255: s = 255
                out[i, j, ch] = int(round(s))
    return out
