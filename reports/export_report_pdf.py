from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

from generate_report import DEFAULT_MART_PATH, DEFAULT_OUTPUT_PATH, render_report


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF_PATH = PROJECT_ROOT / "reports" / "generated" / "narrativeiq_exhibition_report.pdf"


def browser_candidates() -> list[Path]:
    candidates: list[Path] = []
    for executable in ("chrome", "chrome.exe", "msedge", "msedge.exe"):
        found = shutil.which(executable)
        if found:
            candidates.append(Path(found))

    candidates.extend(
        [
            Path("C:/Program Files/Google/Chrome/Application/chrome.exe"),
            Path("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"),
            Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
            Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
        ]
    )
    return candidates


def find_browser() -> Path:
    for candidate in browser_candidates():
        if candidate.exists():
            return candidate
    raise RuntimeError("Chrome or Microsoft Edge was not found. Install one of them to enable PDF export.")


def export_pdf(html_path: Path = DEFAULT_OUTPUT_PATH, pdf_path: Path = DEFAULT_PDF_PATH) -> dict[str, str]:
    if not html_path.exists():
        with DEFAULT_MART_PATH.open("r", encoding="utf-8") as handle:
            mart = json.load(handle)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_report(mart), encoding="utf-8")

    browser = find_browser()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(browser),
        "--headless",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    completed = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, timeout=90)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "Browser PDF export failed."
        raise RuntimeError(detail[-2000:])
    if not pdf_path.exists() or pdf_path.stat().st_size == 0:
        raise RuntimeError("Browser reported success, but the PDF file was not created.")

    return {
        "status": "generated",
        "browser": str(browser),
        "html": str(html_path),
        "pdf": str(pdf_path),
        "bytes": str(pdf_path.stat().st_size),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the NarrativeIQ HTML report to PDF.")
    parser.add_argument("--html", type=Path, default=DEFAULT_OUTPUT_PATH, help="Input HTML report path.")
    parser.add_argument("--output", type=Path, default=DEFAULT_PDF_PATH, help="Output PDF path.")
    args = parser.parse_args()

    print(json.dumps(export_pdf(args.html, args.output)))


if __name__ == "__main__":
    main()
