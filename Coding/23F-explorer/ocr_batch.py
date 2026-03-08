#!/usr/bin/env python3
"""
Batch OCR for 23F-explorer PDFs.
- Runs ocrmypdf (Tesseract, Spanish) on each PDF in pdfs/
- Extracts full text with pdfplumber
- Writes texto_completo field into the matching JSON in data/
- Skips files already processed (texto_completo already set)
- Outputs a summary log

Usage:
    python3 ocr_batch.py [--dry-run] [--force]
"""
import argparse
import glob
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pdfplumber

BASE     = Path(__file__).parent
PDF_DIR  = BASE / "pdfs"
DATA_DIR = BASE / "data"
LOG_FILE = BASE / "ocr_batch.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE)],
)
log = logging.getLogger(__name__)


def find_json_for_pdf(pdf_path: Path) -> Path | None:
    """Find the data JSON whose _meta.filename matches this PDF's filename."""
    pdf_name = pdf_path.name
    for jf in DATA_DIR.glob("*.json"):
        try:
            d = json.loads(jf.read_text())
            if d.get("_meta", {}).get("filename") == pdf_name:
                return jf
        except Exception:
            continue
    return None


def ocr_pdf(pdf_path: Path) -> str:
    """Run ocrmypdf on pdf_path, return extracted text (empty string on failure)."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [
                "ocrmypdf",
                "--language", "spa+eng",
                "--output-type", "pdf",
                "--skip-text",          # skip pages that already have text
                "--rotate-pages",       # auto-rotate
                "--deskew",             # straighten tilted scans
                "--optimize", "0",      # no image compression (speed)
                "--quiet",
                str(pdf_path),
                str(tmp_path),
            ],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode not in (0, 6):   # 6 = already has text
            log.warning(f"ocrmypdf exit {result.returncode} for {pdf_path.name}: {result.stderr[:200]}")
            return ""

        with pdfplumber.open(tmp_path) as pdf:
            pages = []
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    pages.append(t.strip())
            return "\n\n".join(pages)

    except subprocess.TimeoutExpired:
        log.error(f"Timeout processing {pdf_path.name}")
        return ""
    except Exception as e:
        log.error(f"Error processing {pdf_path.name}: {e}")
        return ""
    finally:
        tmp_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done, no changes")
    parser.add_argument("--force",   action="store_true", help="Re-OCR even if texto_completo already set")
    parser.add_argument("--pdf",     help="Process a single PDF file only")
    args = parser.parse_args()

    pdfs = sorted(PDF_DIR.rglob("*.pdf"))
    if args.pdf:
        pdfs = [Path(args.pdf)]

    log.info(f"Found {len(pdfs)} PDFs")

    done = skipped = failed = no_match = 0

    for i, pdf_path in enumerate(pdfs, 1):
        log.info(f"[{i}/{len(pdfs)}] {pdf_path.relative_to(BASE)}")

        json_path = find_json_for_pdf(pdf_path)
        if not json_path:
            log.warning(f"  No matching JSON for {pdf_path.name}")
            no_match += 1
            continue

        data = json.loads(json_path.read_text())
        if data.get("texto_completo") and not args.force:
            log.info(f"  Already processed, skipping")
            skipped += 1
            continue

        if args.dry_run:
            log.info(f"  DRY RUN: would OCR → {json_path.name}")
            continue

        text = ocr_pdf(pdf_path)
        if not text:
            log.warning(f"  OCR produced no text")
            failed += 1
            continue

        data["texto_completo"] = text
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        log.info(f"  ✓ {len(text)} chars → {json_path.name}")
        done += 1

    log.info(f"\nDone: {done}  Skipped: {skipped}  No match: {no_match}  Failed: {failed}")


if __name__ == "__main__":
    main()
