# algorithms/edges.py
import numpy as np

def laplacian_manual(img_np: np.ndarray) -> np.ndarray:
    
    K = np.array([[0,  1, 0],
                  [1, -4, 1],
                  [0,  1, 0]], dtype=np.int32)

    if img_np.ndim == 2:
        src = img_np.astype(np.int32)
        padded = np.pad(src, 1, mode="constant", constant_values=0)
        H, W = src.shape
        out = np.zeros_like(src, dtype=np.int32)

        for i in range(1, H + 1):
            for j in range(1, W + 1):
                region = padded[i-1:i+2, j-1:j+2]
                val = int(np.sum(region * K))
                if val < 0: val = 0
                elif val > 255: val = 255
                out[i-1, j-1] = val

        return out.astype(np.uint8)

    a = img_np.astype(np.int32)
    H, W, C = a.shape
    out = np.zeros_like(a, dtype=np.int32)

    for ch in range(C):
        ch_img = a[:, :, ch]
        padded = np.pad(ch_img, 1, mode="constant", constant_values=0)

        for i in range(1, H + 1):
            for j in range(1, W + 1):
                region = padded[i-1:i+2, j-1:j+2]
                val = int(np.sum(region * K))
                if val < 0: val = 0
                elif val > 255: val = 255
                out[i-1, j-1, ch] = val

    return out.astype(np.uint8)
