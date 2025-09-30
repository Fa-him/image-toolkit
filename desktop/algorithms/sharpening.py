# algorithms/sharpening.py
import numpy as np

def _clip_u8(x):
    x = np.clip(x, 0, 255)
    return x.astype(np.uint8)

def _conv3x3_channel(ch_img: np.ndarray, K: np.ndarray) -> np.ndarray:
    H, W = ch_img.shape
    padded = np.pad(ch_img.astype(np.int32), 1, mode="constant", constant_values=0)
    out = np.empty((H, W), dtype=np.int32)
    for i in range(1, H + 1):
        for j in range(1, W + 1):
            region = padded[i-1:i+2, j-1:j+2]
            out[i-1, j-1] = int(np.sum(region * K))
    return out  # keep int32 for further math

def _apply_kernel_int32(img_np: np.ndarray, K: np.ndarray) -> np.ndarray:
    if img_np.ndim == 2:
        return _conv3x3_channel(img_np, K)
    else:
        H, W, C = img_np.shape
        out = np.empty((H, W, C), dtype=np.int32)
        for ch in range(C):
            out[..., ch] = _conv3x3_channel(img_np[..., ch], K)
        return out

def _abs(x):
    return np.abs(x).astype(np.int32)

# Kernels
SOBEL_X = np.array([[-1, 0, 1],
                    [-2, 0, 2],
                    [-1, 0, 1]], dtype=np.int32)

SOBEL_Y = np.array([[-1, -2, -1],
                    [ 0,  0,  0],
                    [ 1,  2,  1]], dtype=np.int32)

LAPLACIAN_4 = np.array([[0,  1, 0],
                        [1, -4, 1],
                        [0,  1, 0]], dtype=np.int32)

_STRENGTH_ALPHA = {
    "low": 0.5,
    "medium": 1.0,
    "high": 1.5,
}

def _first_order_sharpen(img_np: np.ndarray, alpha: float) -> np.ndarray:
    
    a = img_np.astype(np.int32)
    gx = _apply_kernel_int32(a, SOBEL_X)
    gy = _apply_kernel_int32(a, SOBEL_Y)

    edge = _abs(gx) + _abs(gy)  # simple L1 magnitude
    sharpened = a + (alpha * edge)
    return _clip_u8(sharpened)

def _second_order_sharpen(img_np: np.ndarray, alpha: float) -> np.ndarray:
    
    a = img_np.astype(np.int32)
    lap = _apply_kernel_int32(a, LAPLACIAN_4)
    sharpened = a - (alpha * lap)
    return _clip_u8(sharpened)

def sharpen_image(img_np: np.ndarray, kind: str = "first", strength: str = "medium") -> np.ndarray:
    
    kind = (kind or "first").strip().lower()
    strength = (strength or "medium").strip().lower()
    alpha = _STRENGTH_ALPHA.get(strength, 1.0)

    if kind == "first":
        return _first_order_sharpen(img_np, alpha=alpha)
    elif kind == "second":
        return _second_order_sharpen(img_np, alpha=alpha)
    else:
        return _second_order_sharpen(img_np, alpha=1.0)
