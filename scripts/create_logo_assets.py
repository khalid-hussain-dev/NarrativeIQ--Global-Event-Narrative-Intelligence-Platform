from __future__ import annotations

from pathlib import Path
from shutil import copyfile

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Logo.png"
FRONTEND_LOGOS = ROOT / "frontend" / "public" / "logos"
REPORT_LOGOS = ROOT / "reports" / "assets"


def ensure_dirs() -> None:
    FRONTEND_LOGOS.mkdir(parents=True, exist_ok=True)
    REPORT_LOGOS.mkdir(parents=True, exist_ok=True)


def create_icon(source: Image.Image) -> Image.Image:
    width, height = source.size

    # The uploaded full logo is square, with the orbital mark in the upper half
    # and the wordmark below it. This crop isolates the mark for icon-only usage.
    left = int(width * 0.25)
    upper = int(height * 0.17)
    right = int(width * 0.75)
    lower = int(height * 0.60)
    mark = source.crop((left, upper, right, lower)).convert("RGBA")

    canvas_size = 768
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 6, 24, 0))
    mark.thumbnail((canvas_size - 96, canvas_size - 96), Image.Resampling.LANCZOS)
    x = (canvas_size - mark.width) // 2
    y = (canvas_size - mark.height) // 2
    canvas.alpha_composite(mark, (x, y))
    return canvas


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Logo source not found: {SOURCE}")

    ensure_dirs()
    image = Image.open(SOURCE)

    full_targets = [
        FRONTEND_LOGOS / "narrativeiq-full.png",
        REPORT_LOGOS / "narrativeiq-full.png",
    ]
    for target in full_targets:
        copyfile(SOURCE, target)

    icon = create_icon(image)
    icon.save(FRONTEND_LOGOS / "narrativeiq-icon.png")
    icon.save(REPORT_LOGOS / "narrativeiq-icon.png")

    print("Created logo assets:")
    print(f"- {FRONTEND_LOGOS / 'narrativeiq-full.png'}")
    print(f"- {FRONTEND_LOGOS / 'narrativeiq-icon.png'}")
    print(f"- {REPORT_LOGOS / 'narrativeiq-full.png'}")
    print(f"- {REPORT_LOGOS / 'narrativeiq-icon.png'}")


if __name__ == "__main__":
    main()
