# algorithms/resize.py
import numpy as np

def resize_nearest_manual(img_np: np.ndarray, new_w: int, new_h: int) -> np.ndarray:
    
    assert new_w >= 1 and new_h >= 1, "new size must be >= 1"

    if img_np.ndim == 2:
        src = img_np.astype(np.uint8)
        H, W = src.shape
        out = np.empty((new_h, new_w), dtype=np.uint8)

        for y in range(new_h):
            src_y = int(y * H / new_h)
            if src_y >= H: src_y = H - 1
            for x in range(new_w):
                src_x = int(x * W / new_w)
                if src_x >= W: src_x = W - 1
                out[y, x] = src[src_y, src_x]

        return out

    a = img_np.astype(np.uint8)
    H, W, C = a.shape
    out = np.empty((new_h, new_w, C), dtype=np.uint8)

    for y in range(new_h):
        src_y = int(y * H / new_h)
        if src_y >= H: src_y = H - 1
        for x in range(new_w):
            src_x = int(x * W / new_w)
            if src_x >= W: src_x = W - 1
            out[y, x, :] = a[src_y, src_x, :]

    return out
