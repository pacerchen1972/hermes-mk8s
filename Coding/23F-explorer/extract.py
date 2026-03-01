#!/usr/bin/env python3
"""
23-F Document Extractor
=======================
Processes declassified Spanish coup documents through the Claude API
and extracts structured entities for the knowledge graph visualization.

Budget cap: €300 (~$324 USD). Hard stop at 95% ($308).

Usage:
    python3 extract.py --batch prototype   # 21 priority docs
    python3 extract.py --batch all         # all 153 docs
    python3 extract.py --batch guardia     # Guardia Civil only
    python3 extract.py --status            # show cost/progress
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

import anthropic
import pdfplumber
import fitz  # PyMuPDF

# ── Budget ────────────────────────────────────────────────────────────────────
EUR_TO_USD       = 1.08
BUDGET_EUR       = 300
BUDGET_USD       = BUDGET_EUR * EUR_TO_USD          # ~$324
WARN_AT_USD      = BUDGET_USD * 0.80               # warn at 80%
STOP_AT_USD      = BUDGET_USD * 0.95               # hard stop at 95%

# Haiku 4.5 pricing (per million tokens)
PRICE_INPUT_MTok  = 0.80
PRICE_OUTPUT_MTok = 4.00

# ── Paths ─────────────────────────────────────────────────────────────────────
DOCS_BASE = Path.home() / "Downloads" / "23F"
DATA_DIR  = Path(__file__).parent / "data"
COSTS_FILE = Path(__file__).parent / "costs.json"
DATA_DIR.mkdir(exist_ok=True)

# ── Document batches ──────────────────────────────────────────────────────────
BATCHES = {
    "guardia": [
        ("interior/guardia-civil", "23F_1._Conversacion_telefonica_GARCIA_CARRES_y_Tcol._TEJERO.pdf"),
        ("interior/guardia-civil", "23F_2._Conversacion_telefonica_GARCIA_CARRES.pdf"),
        ("interior/guardia-civil", "23F_3._Conversaciones_telefonicas_unidad_militar_El_Pardo.pdf"),
        ("interior/guardia-civil", "23F_4._Documento_planificacion_del_golpe.pdf"),
        ("interior/guardia-civil", "23F_5._Documento_manuscrito_planificacion_del_golpe.pdf"),
        ("interior/guardia-civil", "23F6TR_1.PDF"),
        ("interior/guardia-civil", "23F_7._Notas_Informativas_2_Seccion_EM_desarrollo_hechos.pdf"),
        ("interior/guardia-civil", "23F_8._Telex_interiores_y_de_Agencias_recibidos_en_2_Seccion_EM.pdf"),
        ("interior/guardia-civil", "23F_9._Oficio_dimanante_Zona_del_Pais_Vasco_disposiciones_sobre_Tejero.pdf"),
        ("interior/guardia-civil", "23F_10._Nota_comparecencia_Tejero_Galaxia.pdf"),
        ("interior/guardia-civil", "23F_11._Nota_Informativa_repercusion_prensa_arresto_Tejero_antes_1981.pdf"),
    ],
    "policia": [
        ("interior/policia", "SITUACION_REGIONES_POLICIALES_24-02-81.pdf"),
        ("interior/policia", "SITUACION_REGIONES_POLICIALES_25-02-81.pdf"),
        ("interior/policia", "SITUACION_REGIONES_POLICIALES_26-02-81.pdf"),
        ("interior/policia", "12-03-81_NOTA_INFORMATIVA_SOBRE_FUERZA_NUEVA.pdf"),
        ("interior/policia", "18-03-81_NOTA_INFORMATIVA_SOBRE_LA_AYUDA_A_LOS_IMPLICADOS_23F.pdf"),
        ("interior/policia", "18-03-81_NOTA_INFORMATIVA_SOBRE_LA_OPERACION_ARIETE.pdf"),
        ("interior/policia", "27-03-81_NOTA_INFORMATIVA_SOBRE_BLOQUEO_DE_CUENTA_DE_ASOC_DE_MUJERES_DE_MILITARES.pdf"),
        ("interior/policia", "11-05-81_NOTA_INFORMATIVA_SOBRE_EL_PCE.pdf"),
        ("interior/policia", "13-05_1.PDF"),
        ("interior/policia", "10-05-83_NOTA_INFORMATIVA_SOBRE_APOYO_ECONOMICO_A_LOS_IMPLICADOS.pdf"),
    ],
    "cni_first10": [
        ("defensa/cni", f"Documento_{i}_R.pdf") for i in range(1, 11)
    ],
}

# Prototype = guardia + first 10 CNI
BATCHES["prototype"] = BATCHES["guardia"] + BATCHES["cni_first10"]

# All documents
def _all_docs():
    docs = []
    for folder, files in [
        ("interior/guardia-civil", [f[1] for f in BATCHES["guardia"]]),
        ("interior/policia",       [f[1] for f in BATCHES["policia"]]),
        ("interior/archivo", [
            "1_PN_Informe_Situacion_12-11-81_desp.pdf",
            "2_Indices_de_subversion_en_las_FAS_DIC_1981.pdf",
            "3_Juicio_del_23-F_desp.pdf",
            "4_campana_contra_SM.pdf",
            "5_INVOLUCIONISMO_POLITICO_PROVOCADO_POSIBLE_GOLPE_MILITAR_desp.pdf",
            "6_POSIBLE_GOLPE_DE_ESTADO_desp.pdf",
            "7_Notas_1983_desp.pdf",
        ]),
    ]:
        docs += [(folder, f) for f in files]
    docs += [("defensa/cni", f"Documento_{i}_R.pdf") for i in range(1, 85)]
    # Add all defensa carpeta files
    for f in Path(DOCS_BASE / "defensa").glob("Carpeta_*.pdf"):
        docs.append(("defensa", f.name))
    for f in Path(DOCS_BASE / "defensa").glob("Causa_*.pdf"):
        docs.append(("defensa", f.name))
    # Foreign affairs
    for sub in ["AGMAE-R39017", "AGMAE-40201", "AGA-83-07633", "AGA-83-08764", "AGA-83-09301"]:
        for f in (DOCS_BASE / "exteriores" / sub).glob("*"):
            docs.append((f"exteriores/{sub}", f.name))
    return docs

BATCHES["all"] = _all_docs()

# ── Cost tracking ─────────────────────────────────────────────────────────────
def load_costs():
    if COSTS_FILE.exists():
        return json.loads(COSTS_FILE.read_text())
    return {"total_usd": 0.0, "total_eur": 0.0, "calls": []}

def save_costs(costs):
    COSTS_FILE.write_text(json.dumps(costs, indent=2, ensure_ascii=False))

def record_cost(costs, doc_id, input_tok, output_tok):
    usd = (input_tok / 1_000_000 * PRICE_INPUT_MTok +
           output_tok / 1_000_000 * PRICE_OUTPUT_MTok)
    costs["total_usd"] += usd
    costs["total_eur"] = costs["total_usd"] / EUR_TO_USD
    costs["calls"].append({
        "doc":           doc_id,
        "input_tokens":  input_tok,
        "output_tokens": output_tok,
        "cost_usd":      round(usd, 6),
        "running_usd":   round(costs["total_usd"], 4),
        "running_eur":   round(costs["total_eur"], 4),
    })
    save_costs(costs)
    return usd

def check_budget(costs):
    total = costs["total_usd"]
    if total >= STOP_AT_USD:
        print(f"\n⛔  BUDGET HARD STOP: ${total:.4f} / ${STOP_AT_USD:.2f} limit reached")
        print(f"    (€{costs['total_eur']:.2f} of €{BUDGET_EUR} budget)")
        sys.exit(1)
    if total >= WARN_AT_USD:
        print(f"⚠️   Budget warning: ${total:.4f} spent (80% of ${BUDGET_USD:.2f})")

# ── PDF reading ───────────────────────────────────────────────────────────────
def extract_text(pdf_path: Path) -> str:
    """Try text extraction; returns empty string if nothing found."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            return "\n\n".join(pages).strip()
    except Exception:
        return ""

def pdf_to_images_b64(pdf_path: Path, max_pages: int = 6) -> list[str]:
    """Render each PDF page as base64-encoded PNG (for scanned/image PDFs)."""
    doc = fitz.open(str(pdf_path))
    images = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        mat = fitz.Matrix(1.5, 1.5)          # 1.5x zoom = ~108 dpi, good balance
        pix = page.get_pixmap(matrix=mat)
        images.append(base64.standard_b64encode(pix.tobytes("png")).decode())
    doc.close()
    return images

# ── Claude extraction ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Eres un historiador experto en la transición española y el 23-F (intento de golpe de estado del 23 de febrero de 1981).
Tu tarea es analizar documentos desclasificados del gobierno español y extraer información estructurada.
Responde ÚNICAMENTE con JSON válido, sin texto adicional, sin bloques de código markdown."""

EXTRACTION_PROMPT = """Analiza este documento desclasificado sobre el 23-F y extrae la siguiente información en JSON:

{
  "titulo_es": "título descriptivo en español (máx 80 chars)",
  "titulo_en": "descriptive title in English (max 80 chars)",
  "fecha_documento": "YYYY-MM-DD o null si desconocida",
  "periodo": "pre-golpe|golpe|post-golpe|juicio|otro",
  "clasificacion_original": "SECRETO|RESERVADO|CONFIDENCIAL|sin_clasificar",
  "tipo_documento": "transcripcion_telefonica|informe|oficio|nota_informativa|telex|manuscrito|otro",
  "ministerio": "Interior|Defensa|Exteriores",
  "resumen_es": "resumen de 2-3 frases en español",
  "resumen_en": "2-3 sentence summary in English",
  "personas": [
    {
      "nombre": "nombre completo normalizado",
      "cargo": "cargo oficial",
      "organizacion": "organización",
      "rol_en_23f": "conspirador|leal|neutral|víctima|testigo",
      "acciones": ["acción concreta mencionada en el documento"]
    }
  ],
  "organizaciones": [
    {
      "nombre": "nombre de la organización",
      "tipo": "militar|policial|gubernamental|político|inteligencia|otro"
    }
  ],
  "eventos": [
    {
      "fecha": "YYYY-MM-DD o descripción aproximada",
      "descripcion_es": "qué ocurrió",
      "descripcion_en": "what happened",
      "lugar": "lugar si se menciona"
    }
  ],
  "citas_clave": [
    {
      "autor": "quién lo dijo o escribió",
      "texto": "cita literal en español",
      "traduccion_en": "English translation",
      "importancia": "por qué es significativa"
    }
  ],
  "relaciones": [
    {
      "origen": "persona u organización",
      "destino": "persona u organización",
      "tipo": "llamó|ordenó|informó|coordinó|apoyó|se_opuso|detuvo|juzgó|financió",
      "descripcion": "contexto breve",
      "fecha": "YYYY-MM-DD o null"
    }
  ],
  "temas": ["lista de tags relevantes, ej: comunicaciones, planificacion, reaccion-internacional, juicio"],
  "ilegible": false
}

Si el documento es completamente ilegible, devuelve: {"ilegible": true, "titulo_es": "Documento ilegible"}"""

def call_claude_text(client, text: str, doc_id: str) -> tuple[dict, int, int]:
    """Send text document to Claude for extraction."""
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"{EXTRACTION_PROMPT}\n\n--- DOCUMENTO ---\n\n{text[:12000]}"
        }]
    )
    raw = msg.content[0].text
    data = json.loads(raw)
    return data, msg.usage.input_tokens, msg.usage.output_tokens

def call_claude_images(client, images_b64: list[str], doc_id: str) -> tuple[dict, int, int]:
    """Send image pages to Claude Vision for extraction."""
    content = [{"type": "text", "text": EXTRACTION_PROMPT + "\n\n--- DOCUMENTO (imágenes) ---"}]
    for img_b64 in images_b64:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": img_b64}
        })
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}]
    )
    raw = msg.content[0].text
    data = json.loads(raw)
    return data, msg.usage.input_tokens, msg.usage.output_tokens

# ── Main processing ───────────────────────────────────────────────────────────
def process_doc(client, folder: str, filename: str, costs: dict) -> bool:
    """
    Process a single document. Returns True if successful.
    Skips if already processed (data/{doc_id}.json exists).
    """
    doc_id = filename.replace(".pdf", "").replace(".PDF", "").replace(".jpg", "")
    out_path = DATA_DIR / f"{doc_id}.json"

    if out_path.exists():
        print(f"  ⏭  skip (already done): {filename}")
        return True

    pdf_path = DOCS_BASE / folder / filename

    # Skip image files (jpg) for now — add image handling if needed
    if filename.lower().endswith(".jpg"):
        print(f"  🖼  skip image file (JPG): {filename}")
        return True

    if not pdf_path.exists():
        print(f"  ❌  file not found: {pdf_path}")
        return False

    check_budget(costs)

    # Try text extraction first
    text = extract_text(pdf_path)
    is_image_pdf = len(text) < 100

    try:
        if is_image_pdf:
            print(f"  🖼  image PDF → vision: {filename}")
            images = pdf_to_images_b64(pdf_path)
            if not images:
                print(f"  ❌  no pages found: {filename}")
                return False
            data, in_tok, out_tok = call_claude_images(client, images, doc_id)
        else:
            print(f"  📄  text PDF → extract: {filename} ({len(text)} chars)")
            data, in_tok, out_tok = call_claude_text(client, text, doc_id)
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON parse error for {filename}: {e}")
        return False
    except Exception as e:
        print(f"  ❌  API error for {filename}: {e}")
        time.sleep(2)
        return False

    # Enrich with metadata
    data["_meta"] = {
        "doc_id":       doc_id,
        "filename":     filename,
        "folder":       folder,
        "is_image_pdf": is_image_pdf,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
    }

    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    cost = record_cost(costs, doc_id, in_tok, out_tok)
    print(f"  ✅  done: {doc_id} | ${cost:.5f} | running: ${costs['total_usd']:.4f} (€{costs['total_eur']:.2f})")
    time.sleep(0.3)  # gentle rate limiting
    return True

def print_status(costs):
    calls = len(costs["calls"])
    total_usd = costs["total_usd"]
    total_eur = costs["total_eur"]
    processed = len(list(DATA_DIR.glob("*.json")))
    print(f"\n{'='*50}")
    print(f"  Documents processed : {processed}")
    print(f"  API calls made      : {calls}")
    print(f"  Total spent         : ${total_usd:.4f} USD / €{total_eur:.2f}")
    print(f"  Budget remaining    : €{BUDGET_EUR - total_eur:.2f} of €{BUDGET_EUR}")
    print(f"  Budget used         : {total_usd/BUDGET_USD*100:.1f}%")
    print(f"{'='*50}\n")

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="23-F Document Extractor")
    parser.add_argument("--batch", choices=["prototype", "all", "guardia", "policia", "cni_first10"],
                        default="prototype", help="Which document batch to process")
    parser.add_argument("--status", action="store_true", help="Show cost/progress status")
    args = parser.parse_args()

    costs = load_costs()

    if args.status:
        print_status(costs)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌  ANTHROPIC_API_KEY not set in environment")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    docs = BATCHES[args.batch]

    print(f"\n🗂  23-F Extractor — batch: {args.batch}")
    print(f"   Documents to process : {len(docs)}")
    print(f"   Budget               : €{BUDGET_EUR} (hard stop at €{STOP_AT_USD/EUR_TO_USD:.0f})")
    print(f"   Already spent        : €{costs['total_eur']:.2f}\n")

    ok = fail = skip = 0
    for folder, filename in docs:
        out_id = filename.replace(".pdf", "").replace(".PDF", "")
        if (DATA_DIR / f"{out_id}.json").exists():
            skip += 1
        elif process_doc(client, folder, filename, costs):
            ok += 1
        else:
            fail += 1

    print(f"\n📊  Batch complete — OK:{ok} | Skipped:{skip} | Failed:{fail}")
    print_status(costs)
    print("→  Run: python3 build_viz.py   to generate the visualization")

if __name__ == "__main__":
    main()
