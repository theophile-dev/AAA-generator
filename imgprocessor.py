from pathlib import Path
from typing import List
import numpy as np
from PIL import Image, ImageFilter

IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}

def rgb_to_hsv_sv(rgb_arr: np.ndarray):
    """Return (saturation, value) in [0,1] from uint8 RGB array [H, W, 3]."""
    arr = rgb_arr.astype(np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    cmax = np.maximum.reduce([r, g, b])
    cmin = np.minimum.reduce([r, g, b])
    delta = cmax - cmin + 1e-6
    v = cmax
    s = delta / (cmax + 1e-6)
    return s, v

def remove_white_bg(img: Image.Image,
                    rgb_min: int = 240,
                    v_min: float = 0.95,
                    s_max: float = 0.20,
                    feather: int = 1) -> Image.Image:
    """Make white/near-white pixels transparent."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    arr = np.array(img)
    rgb = arr[..., :3]
    alpha = arr[..., 3].astype(np.float32) / 255.0

    keep_transparent = alpha < 0.01
    rule_rgb = (rgb[..., 0] >= rgb_min) & (rgb[..., 1] >= rgb_min) & (rgb[..., 2] >= rgb_min)
    s, v = rgb_to_hsv_sv(rgb)
    rule_hsv = (v >= v_min) & (s <= s_max)
    whiteish = (rule_rgb | rule_hsv) & (~keep_transparent)

    if np.all(alpha >= 0.99):
        new_alpha = np.where(whiteish, 0.0, 1.0)
    else:
        new_alpha = np.where(whiteish, 0.0, alpha)

    if feather > 0:
        mask = Image.fromarray((new_alpha * 255).astype(np.uint8), mode="L")
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))
        new_alpha = np.array(mask).astype(np.float32) / 255.0

    out = arr.copy()
    out[..., 3] = (new_alpha * 255.0).clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, mode="RGBA")

def trim_to_content(img: Image.Image, pad: int = 1) -> Image.Image:
    """Trim transparent borders to fit content."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = np.array(img.split()[-1])
    nz = np.where(alpha > 5)
    if nz[0].size == 0:
        return img

    top, bottom = int(nz[0].min()), int(nz[0].max())
    left, right = int(nz[1].min()), int(nz[1].max())
    left = max(left - pad, 0)
    top = max(top - pad, 0)
    right = min(right + pad, img.width - 1)
    bottom = min(bottom + pad, img.height - 1)

    return img.crop((left, top, right + 1, bottom + 1))

def process_images(src_folder: Path,
                   rgb_min: int = 240,
                   v_min: float = 0.95,
                   s_max: float = 0.20,
                   feather: int = 1,
                   pad: int = 1) -> List[Path]:
    """
    Remove white background & crop all images in src_folder.
    Returns list of output file paths.
    """


    img_paths = [p for p in src_folder.iterdir() if p.suffix.lower() in IMG_EXTS and p.is_file()]
    out_paths = []

    for path in img_paths:
        img = Image.open(path)
        no_bg = remove_white_bg(img, rgb_min=rgb_min, v_min=v_min, s_max=s_max, feather=feather)
        trimmed = trim_to_content(no_bg, pad=pad)
        w, h = trimmed.size
        new_name = f"{w}x{h}_{path.name}"
        out_path = path.with_name(new_name)
        trimmed.save(out_path, "PNG")
        ##delete original file
        path.unlink(missing_ok=True)
        out_paths.append(out_path)
    return out_paths
