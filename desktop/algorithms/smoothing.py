# algorithms/smoothing.py
import numpy as np

def _clip_u8(x):
    x = np.clip(x, 0, 255)
    return x.astype(np.uint8)

def _conv3x3_channel(ch_img: np.ndarray, K: np.ndarray) -> np.ndarray:
    H, W = ch_img.shape
    padded = np.pad(ch_img.astype(np.int32), 1, mode="constant", constant_values=0)
    out = np.empty((H, W), dtype=np.int32)
    # explicit loops (manual implementation)
    for i in range(1, H + 1):
        for j in range(1, W + 1):
            region = padded[i-1:i+2, j-1:j+2]
            out[i-1, j-1] = int(np.sum(region * K))
    return _clip_u8(out)

def _apply_kernel(img_np: np.ndarray, K: np.ndarray, passes: int = 1) -> np.ndarray:
    out = img_np.copy()
    for _ in range(max(1, passes)):
        if out.ndim == 2:
            out = _conv3x3_channel(out, K)
        else:
            H, W, C = out.shape
            tmp = np.empty_like(out)
            for ch in range(C):
                tmp[..., ch] = _conv3x3_channel(out[..., ch], K)
            out = tmp
    return out

def mean_kernel() -> np.ndarray:
    return (np.ones((3, 3), dtype=np.float32) / 9.0)

def weighted_kernel() -> np.ndarray:
    return (np.array([[1, 2, 1],
                      [2, 4, 2],
                      [1, 2, 1]], dtype=np.float32) / 16.0)

def gaussian_kernel() -> np.ndarray:
    # Per your requirement: same as weighted averaging
    return weighted_kernel()

_STRENGTH_TO_PASSES = {
    "low": 1,
    "medium": 2,
    "high": 3,
}

def smooth_image(img_np: np.ndarray, mode: str = "mean", strength: str = "medium") -> np.ndarray:
    
    mode = (mode or "mean").strip().lower()
    strength = (strength or "medium").strip().lower()
    passes = _STRENGTH_TO_PASSES.get(strength, 2)

    if mode == "mean":
        K = mean_kernel()
    elif mode == "weighted":
        K = weighted_kernel()
    elif mode == "gaussian":
        K = gaussian_kernel()
    else:
        # default to mean if unknown
        K = mean_kernel()

    return _apply_kernel(img_np, K, passes=passes)
