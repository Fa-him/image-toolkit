from PIL import Image
from pathlib import Path

# Use raw string r"" or double backslashes \\ to avoid escape errors
src = Path(r"C:\32\Image Toolkit\image-toolkit\assets\app.png")
dst = Path(r"C:\32\Image Toolkit\image-toolkit\assets\app.ico")

img = Image.open(src).convert("RGBA")
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
img.save(dst, format="ICO", sizes=sizes)
print(f"Saved {dst.resolve()}")
