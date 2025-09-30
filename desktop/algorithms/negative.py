# algorithms/negative.py
import numpy as np

def _to_grayscale_manual(rgb: np.ndarray) -> np.ndarray:
    
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    gray = (0.299*r + 0.587*g + 0.114*b).astype(np.uint8)
    return gray

def image_negative_exact(img_np: np.ndarray, force_gray: bool = True) -> np.ndarray:
   
    if force_gray:
        if img_np.ndim == 3:
            img_gray = _to_grayscale_manual(img_np)
        else:
            img_gray = img_np.copy()
    else:
        if img_np.ndim == 2:
            img_np = np.stack([img_np, img_np, img_np], axis=2)
        img_gray = None 

    if img_gray is not None:
        
        temp = img_gray.copy() 

        max_pixel = int(np.max(img_gray))
        
        if max_pixel <= 0:
            L_minus_1 = 255  
        else:
            L_minus_1 = int((2 ** (np.ceil(np.log2(max_pixel)))) - 1)

        h, w = img_gray.shape[0], img_gray.shape[1]
        neg = img_gray.copy()

        for i in range(h):
            for j in range(w):
                neg[i, j] = L_minus_1 - img_gray[i, j]

        out3 = np.stack([neg, neg, neg], axis=2).astype(np.uint8)
        return out3
    else:
        a = img_np.copy()
        h, w, c = a.shape
        out = np.zeros_like(a)

        for ch in range(3):
            max_pixel = int(np.max(a[:,:,ch]))
            if max_pixel <= 0:
                L_minus_1 = 255
            else:
                L_minus_1 = int((2 ** (np.ceil(np.log2(max_pixel)))) - 1)

            for i in range(h):
                for j in range(w):
                    out[i, j, ch] = L_minus_1 - a[i, j, ch]

        return out.astype(np.uint8)

def negative_curve_points(img_np: np.ndarray, force_gray: bool = True):
    
    if force_gray:
        if img_np.ndim == 3:
            img_gray = _to_grayscale_manual(img_np)
        else:
            img_gray = img_np
        max_pixel = int(np.max(img_gray))
    else:
        max_pixel = int(np.max(img_np))

    if max_pixel <= 0:
        L_minus_1 = 255
    else:
        L_minus_1 = int((2 ** (np.ceil(np.log2(max_pixel)))) - 1)

    if force_gray:
        r = np.unique(img_gray)
    else:
        r = np.unique(img_np)

    s = np.zeros(len(r), dtype=np.float32)
    for i in range(len(r)):
        s[i] = L_minus_1 - r[i]
    return r, s
