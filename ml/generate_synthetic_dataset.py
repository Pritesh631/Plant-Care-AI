from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
CLASS_NAMES_PATH = ROOT / "models" / "class_names.json"
DATASET_ROOT = ROOT / "ml" / "dataset"


def make_leaf_image(disease: str, index: int) -> Image.Image:
    width, height = 224, 224
    img = Image.new("RGB", (width, height), color=(245, 248, 241))
    draw = ImageDraw.Draw(img)

    leaf_color = (68, 145, 62)
    if "healthy" in disease:
        leaf_color = (72, 168, 70)
    elif "late" in disease or "blight" in disease or "spot" in disease:
        leaf_color = (98, 135, 58)
    elif "rust" in disease:
        leaf_color = (154, 110, 52)
    elif "mildew" in disease or "powdery" in disease:
        leaf_color = (190, 181, 155)
    elif "virus" in disease or "curl" in disease:
        leaf_color = (112, 160, 66)
    elif "mosaic" in disease:
        leaf_color = (84, 148, 70)
    else:
        leaf_color = (90, 160, 82)

    # Leaf silhouette
    leaf_points = [
        (112, 28), (154, 26), (182, 54), (192, 94), (198, 130), (190, 164),
        (170, 194), (146, 210), (110, 218), (85, 200), (74, 162), (62, 116),
        (66, 80), (84, 48)
    ]
    draw.polygon(leaf_points, fill=leaf_color)
    draw.line((112, 28, 112, 218), fill=(42, 92, 40), width=3)
    for x in [88, 98, 108, 120, 130, 142, 154, 165]:
        draw.line((x, 30, x, 210), fill=(50, 110, 45), width=1)

    if "healthy" in disease:
        # Healthy leaf: light speckles and a small green variation
        for _ in range(18):
            x = random.randint(60, 180)
            y = random.randint(60, 180)
            r = random.randint(2, 7)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(110, 190, 100))
    else:
        # Diseased leaf: lesions / spots / mildew / rust patterns
        for _ in range(random.randint(12, 24)):
            x = random.randint(40, 190)
            y = random.randint(40, 190)
            w = random.randint(8, 24)
            h = random.randint(8, 24)
            if "mildew" in disease or "powdery" in disease:
                fill = (230, 230, 220)
            elif "rust" in disease:
                fill = (176, 92, 25)
            elif "black" in disease or "rot" in disease:
                fill = (90, 60, 45)
            elif "spot" in disease or "blight" in disease or "leaf" in disease:
                fill = (160, 88, 48)
            elif "virus" in disease or "curl" in disease:
                fill = (145, 70, 56)
            else:
                fill = (150, 84, 42)
            draw.ellipse((x - w, y - h, x + w, y + h), fill=fill)

    # background noise and vignette
    for _ in range(180):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        if (x - 112) ** 2 + (y - 112) ** 2 < 8000:
            img.putpixel((x, y), (random.randint(0, 20), random.randint(0, 20), random.randint(0, 20)))

    img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
    return img


def generate_dataset() -> None:
    if DATASET_ROOT.exists():
        shutil.rmtree(DATASET_ROOT)
    DATASET_ROOT.mkdir(parents=True, exist_ok=True)

    class_names = json.loads(CLASS_NAMES_PATH.read_text())
    for class_name in class_names:
        class_dir = DATASET_ROOT / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        disease = class_name.split("___")[-1].lower()
        for idx in range(10):
            img = make_leaf_image(disease, idx)
            img.save(class_dir / f"{idx}.jpg", quality=85)

    print(f"Created synthetic dataset with {len(class_names)} classes under {DATASET_ROOT}")


if __name__ == "__main__":
    random.seed(42)
    generate_dataset()
