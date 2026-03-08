#!/usr/bin/env python3
"""
Batch translation for 23F-explorer OCR texts.

For each JSON in data/ that has a texto_completo field:
  - Renames it to texto_completo_es (Spanish is the primary language)
  - Detects if source is actually English (some Exteriores docs are US cables)
  - Translates ES→EN  (or EN→ES for English-source docs)
  - Stores both as texto_completo_es and texto_completo_en

Google Translate via deep_translator — free, no API key required.

Usage:
    python3 translate_batch.py [--dry-run] [--force] [--limit N]
"""
import argparse
import json
import logging
import time
from pathlib import Path

from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException

BASE     = Path(__file__).parent
DATA_DIR = BASE / "data"
LOG_FILE = BASE / "translate_batch.log"

# Google Translate max chunk size (chars)
CHUNK_SIZE = 4500

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE)],
)
log = logging.getLogger(__name__)


def detect_lang(text: str) -> str:
    """Detect language of text, return 'es' or 'en' (default 'es' on failure)."""
    try:
        lang = detect(text[:1000])
        return lang if lang in ("es", "en") else "es"
    except LangDetectException:
        return "es"


def translate_text(text: str, source: str, target: str) -> str:
    """Translate text in chunks to stay under Google Translate limits."""
    if not text.strip():
        return ""
    if source == target:
        return text

    translator = GoogleTranslator(source=source, target=target)
    chunks = []
    # Split on double-newline (paragraph boundaries) first
    paragraphs = text.split("\n\n")
    current_chunk = []
    current_len = 0

    for para in paragraphs:
        if current_len + len(para) > CHUNK_SIZE and current_chunk:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [para]
            current_len = len(para)
        else:
            current_chunk.append(para)
            current_len += len(para) + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    translated_chunks = []
    for i, chunk in enumerate(chunks):
        try:
            result = translator.translate(chunk)
            translated_chunks.append(result or "")
            if len(chunks) > 1:
                time.sleep(0.3)  # polite rate limiting
        except Exception as e:
            log.warning(f"  Translation error on chunk {i+1}/{len(chunks)}: {e}")
            translated_chunks.append(chunk)  # fall back to original

    return "\n\n".join(translated_chunks)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force",   action="store_true", help="Re-translate even if already done")
    parser.add_argument("--limit",   type=int, default=0, help="Process only first N files")
    args = parser.parse_args()

    json_files = sorted(DATA_DIR.glob("*.json"))
    done = skipped_done = skipped_no_ocr = failed = 0

    for i, jf in enumerate(json_files):
        if args.limit and i >= args.limit:
            break

        data = json.loads(jf.read_text())

        # Skip if no OCR text at all
        raw = data.get("texto_completo") or data.get("texto_completo_es")
        if not raw:
            skipped_no_ocr += 1
            continue

        # Skip if already translated (both langs present) unless --force
        if data.get("texto_completo_es") and data.get("texto_completo_en") and not args.force:
            log.info(f"[{i+1}] {jf.name} — already translated, skipping")
            skipped_done += 1
            continue

        log.info(f"[{i+1}] {jf.name} ({len(raw)} chars)")

        if args.dry_run:
            lang = detect_lang(raw)
            log.info(f"  DRY RUN: detected={lang}, would translate {lang}↔{'en' if lang=='es' else 'es'}")
            continue

        try:
            lang = detect_lang(raw)
            log.info(f"  Detected: {lang}")

            if lang == "es":
                text_es = raw
                log.info(f"  Translating ES→EN ({len(raw)} chars)…")
                text_en = translate_text(raw, "es", "en")
            else:  # en or unknown → treat as EN
                text_en = raw
                log.info(f"  Translating EN→ES ({len(raw)} chars)…")
                text_es = translate_text(raw, "en", "es")

            # Write back — remove old key, set both language keys
            data.pop("texto_completo", None)
            data["texto_completo_es"] = text_es
            data["texto_completo_en"] = text_en

            jf.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            log.info(f"  ✓ ES:{len(text_es)} chars  EN:{len(text_en)} chars")
            done += 1

        except Exception as e:
            log.error(f"  FAILED: {e}")
            failed += 1

    log.info(f"\nDone: {done}  Already done: {skipped_done}  No OCR: {skipped_no_ocr}  Failed: {failed}")


if __name__ == "__main__":
    main()
