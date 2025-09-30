# Image Processing Toolkit

Manual (no OpenCV) GUI toolkit for classic image operations (Tkinter + ttkbootstrap).
- Negative, Threshold, Smoothing (Mean/Weighted/Gaussian), Sharpening (1st/2nd order),
  Laplacian Edge, Histogram (rendered), Log/Gamma, Manual Resize, etc.

## Repo layout
- `desktop/` — Windows app (Tkinter)
- `web/` — Web version (coming soon)

## Build (local)
```bash
cd desktop
pip install -r requirements.txt
pyinstaller --name "Image Processing Toolkit" --onefile --windowed --noconfirm --add-data "assets;assets" --collect-all ttkbootstrap --icon "assets/app.ico" app.py
