#!/usr/bin/env python3
"""
23-F Visualization Builder
===========================
Reads extracted JSON files from data/ and generates a self-contained
interactive HTML knowledge graph + timeline.

Usage:
    python3 build_viz.py
    → produces index.html
"""

import json
import os
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

DATA_DIR     = Path(__file__).parent / "data"
PROFILES_DIR = Path(__file__).parent / "data" / "profiles"
OUTPUT       = Path(__file__).parent / "index.html"
DOCS_BASE    = Path.home() / "Downloads" / "23F"
VENDOR_DIR = Path(__file__).parent / "vendor"
VENDOR_D3  = VENDOR_DIR / "d3.min.js"
D3_URL     = "https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"


def ensure_d3():
    """H-1: Vendor D3 locally to avoid CDN SRI risk."""
    if not VENDOR_D3.exists():
        VENDOR_DIR.mkdir(exist_ok=True)
        print("⬇  Downloading D3 v7.9.0 to vendor/d3.min.js…")
        urllib.request.urlretrieve(D3_URL, VENDOR_D3)
        print(f"✅  D3 vendored ({VENDOR_D3.stat().st_size // 1024} KB)")
    else:
        print(f"✓  D3 already vendored ({VENDOR_D3.stat().st_size // 1024} KB)")

# ── Load all extracted documents ──────────────────────────────────────────────
def load_docs():
    docs = []
    for path in sorted(DATA_DIR.glob("*.json")):
        try:
            d = json.loads(path.read_text())
            if not d.get("ilegible"):
                docs.append(d)
        except Exception as e:
            print(f"  ⚠  skip {path.name}: {e}")
    return docs


def slugify_name(s: str) -> str:
    """Slugify for profile lookup (shared with build_graph slugify)."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s


def load_profiles() -> dict:
    """Load enriched person profiles from data/profiles/*.json.
    Returns a dict keyed by slugified name for fast lookup, covering aliases."""
    profiles = {}
    if not PROFILES_DIR.exists():
        return profiles
    count = 0
    for path in sorted(PROFILES_DIR.glob("*.json")):
        try:
            p = json.loads(path.read_text())
            for name in [p.get("nombre", "")] + p.get("aliases", []):
                if name:
                    profiles[slugify_name(name)] = p
            count += 1
        except Exception as e:
            print(f"  ⚠  skip profile {path.name}: {e}")
    print(f"👤  Loaded {count} person profiles")
    return profiles


# ── Build graph data ──────────────────────────────────────────────────────────
NODE_COLORS = {
    "person":       "#e05252",   # red
    "organization": "#4a90d9",   # blue
    "event":        "#f0b429",   # amber
    "document":     "#38c77e",   # green
}

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s

def build_graph(docs: list, profiles: dict = None) -> dict:
    nodes = {}   # id → node dict
    edges = []   # list of edge dicts
    node_id_counter = [0]

    def get_or_create(label: str, node_type: str, extra: dict = None) -> str:
        key = f"{node_type}:{slugify(label)}"
        if key not in nodes:
            node_id_counter[0] += 1
            nodes[key] = {
                "id":    key,
                "label": label,
                "type":  node_type,
                "color": NODE_COLORS[node_type],
                "docs":  [],
                **(extra or {}),
            }
        return key

    for doc in docs:
        meta    = doc.get("_meta", {})
        doc_id  = meta.get("doc_id", "unknown")
        folder  = meta.get("folder", "")
        fname   = meta.get("filename", "")

        # Document node
        doc_label = doc.get("titulo_es", doc_id)[:60]
        doc_node_id = get_or_create(doc_label, "document", {
            "doc_id":       doc_id,
            "filename":     fname,
            "folder":       folder,
            "titulo_es":    doc.get("titulo_es", ""),
            "titulo_en":    doc.get("titulo_en", ""),
            "resumen_es":   doc.get("resumen_es", ""),
            "resumen_en":   doc.get("resumen_en", ""),
            "fecha":        doc.get("fecha_documento"),
            "periodo":      doc.get("periodo", ""),
            "clasificacion": doc.get("clasificacion_original", ""),
            "tipo":         doc.get("tipo_documento", ""),
            "ministerio":   doc.get("ministerio", ""),
            "citas":        doc.get("citas_clave", []),
            "temas":        doc.get("temas", []),
        })

        # People
        for person in doc.get("personas", []):
            nombre = person.get("nombre", "").strip()
            if not nombre or len(nombre) < 3:
                continue
            # Merge enriched profile if available; use canonical name to deduplicate
            # variants like "Antonio Tejero" vs "Antonio Tejero Molina"
            prof = (profiles or {}).get(slugify_name(nombre), {})
            canonical_nombre = prof.get("nombre", nombre)
            pid = get_or_create(canonical_nombre, "person", {
                "cargo":           prof.get("cargo_en_23f") or person.get("cargo", ""),
                "org":             person.get("organizacion", ""),
                "rol_23f":         prof.get("rol_23f") or person.get("rol_en_23f", ""),
                "nombre_completo": prof.get("nombre_completo", nombre),
                "fecha_nac":       prof.get("fecha_nacimiento", ""),
                "fecha_def":       prof.get("fecha_fallecimiento", ""),
                "descripcion_es":  prof.get("descripcion_es", ""),
                "descripcion_en":  prof.get("descripcion_en", ""),
                "acciones_23f":    prof.get("acciones_23f", []),
                "condena":         prof.get("condena", ""),
                "wikipedia_es":    prof.get("wikipedia_es", ""),
                "wikipedia_en":    prof.get("wikipedia_en", ""),
            })
            nodes[pid]["docs"].append(doc_node_id)
            edges.append({
                "source": pid,
                "target": doc_node_id,
                "type":   "mentioned_in",
                "label":  "mencionado en",
            })
            # Link person → their organization
            org_name = person.get("organizacion", "").strip()
            if org_name and len(org_name) > 2:
                oid = get_or_create(org_name, "organization")
                edges.append({
                    "source": pid,
                    "target": oid,
                    "type":   "member_of",
                    "label":  "pertenece a",
                })

        # Organizations (standalone)
        for org in doc.get("organizaciones", []):
            oname = org.get("nombre", "") if isinstance(org, dict) else str(org)
            oname = oname.strip()
            if not oname or len(oname) < 2:
                continue
            oid = get_or_create(oname, "organization", {
                "tipo_org": org.get("tipo", "") if isinstance(org, dict) else ""
            })
            nodes[oid]["docs"].append(doc_node_id)

        # Events
        for ev in doc.get("eventos", []):
            desc = ev.get("descripcion_es", "").strip()
            if not desc or len(desc) < 5:
                continue
            desc_short = desc[:60] + ("…" if len(desc) > 60 else "")
            eid = get_or_create(desc_short, "event", {
                "fecha":        ev.get("fecha"),
                "desc_es":      ev.get("descripcion_es", ""),
                "desc_en":      ev.get("descripcion_en", ""),
                "lugar":        ev.get("lugar", ""),
            })
            edges.append({
                "source": doc_node_id,
                "target": eid,
                "type":   "documents_event",
                "label":  "documenta",
            })

        # Explicit relationships
        for rel in doc.get("relaciones", []):
            src_name = rel.get("origen", "").strip()
            tgt_name = rel.get("destino", "").strip()
            if not src_name or not tgt_name:
                continue
            # Try to find existing nodes by fuzzy match, else create person nodes
            src_key = next((k for k in nodes if slugify(src_name) in k), None)
            tgt_key = next((k for k in nodes if slugify(tgt_name) in k), None)
            if not src_key:
                src_key = get_or_create(src_name, "person")
            if not tgt_key:
                tgt_key = get_or_create(tgt_name, "person")
            edges.append({
                "source":    src_key,
                "target":    tgt_key,
                "type":      rel.get("tipo", "relacionado"),
                "label":     rel.get("tipo", ""),
                "desc":      rel.get("descripcion", ""),
                "fecha":     rel.get("fecha"),
            })

    # Compute node sizes by connection count
    degree = defaultdict(int)
    for e in edges:
        degree[e["source"]] += 1
        degree[e["target"]] += 1
    for nid, node in nodes.items():
        node["size"] = max(8, min(30, 8 + degree[nid] * 2))

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
    }

# ── Build timeline data ───────────────────────────────────────────────────────
def build_timeline(docs: list) -> list:
    events = []
    seen = set()
    for doc in docs:
        fecha = doc.get("fecha_documento")
        titulo = doc.get("titulo_es", "")
        if fecha and titulo not in seen:
            seen.add(titulo)
            events.append({
                "date":    fecha,
                "title":   titulo[:50],
                "title_en": doc.get("titulo_en", "")[:50],
                "period":  doc.get("periodo", ""),
                "doc_id":  doc.get("_meta", {}).get("doc_id", ""),
            })
        for ev in doc.get("eventos", []):
            desc = ev.get("descripcion_es", "")[:50]
            if desc and desc not in seen and (ev.get("fecha") or "").startswith("19"):
                seen.add(desc)
                events.append({
                    "date":    ev.get("fecha", ""),
                    "title":   desc,
                    "title_en": ev.get("descripcion_en", "")[:50],
                    "period":  doc.get("periodo", ""),
                    "doc_id":  doc.get("_meta", {}).get("doc_id", ""),
                })
    events.sort(key=lambda x: x.get("date", "9999"))
    return events

# ── Generate HTML ─────────────────────────────────────────────────────────────
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'self' data:; base-uri 'self'; form-action 'none'; object-src 'none'">
<title>23-F — Mapa de Conocimiento / Knowledge Map</title>
<script src="vendor/d3.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0d1117; color: #e6edf3; height: 100vh; display: flex; flex-direction: column; }

  /* ── Header ── */
  header { padding: 12px 20px; background: #161b22; border-bottom: 1px solid #30363d;
            display: flex; align-items: center; gap: 16px; flex-shrink: 0; }
  header h1 { font-size: 18px; font-weight: 700; color: #f0b429; letter-spacing: 1px; }
  header span { font-size: 12px; color: #8b949e; }
  .lang-toggle { margin-left: auto; display: flex; gap: 8px; }
  .lang-toggle button { padding: 4px 10px; border-radius: 4px; border: 1px solid #30363d;
                         background: #21262d; color: #e6edf3; cursor: pointer; font-size: 12px; }
  .lang-toggle button.active { background: #f0b429; color: #0d1117; border-color: #f0b429; }

  /* ── Filter bar ── */
  .filters { padding: 8px 20px; background: #161b22; border-bottom: 1px solid #30363d;
              display: flex; gap: 10px; align-items: center; flex-wrap: wrap; flex-shrink: 0; }
  .filters label { font-size: 12px; color: #8b949e; }
  .filter-btn { padding: 4px 12px; border-radius: 20px; border: none; cursor: pointer;
                font-size: 12px; font-weight: 600; opacity: 0.4; transition: opacity .2s; }
  .filter-btn.active { opacity: 1; }
  .filter-btn.person       { background: #e05252; color: #fff; }
  .filter-btn.organization { background: #4a90d9; color: #fff; }
  .filter-btn.event        { background: #f0b429; color: #000; }
  .filter-btn.document     { background: #38c77e; color: #000; }
  .search-box { margin-left: auto; padding: 5px 10px; border-radius: 6px;
                border: 1px solid #30363d; background: #21262d; color: #e6edf3;
                font-size: 13px; width: 220px; }
  .search-box::placeholder { color: #8b949e; }

  /* ── Main layout ── */
  .main { display: flex; flex: 1; overflow: hidden; min-height: 80px; }

  /* ── Graph ── */
  #graph-container { flex: 1; position: relative; overflow: hidden; }
  svg { width: 100%; height: 100%; }
  .node circle { stroke: #0d1117; stroke-width: 2; cursor: pointer; transition: opacity .2s, stroke .15s, stroke-width .15s; }
  .node:hover circle { stroke: #e6edf3; stroke-width: 3; filter: brightness(1.3); }
  .node text { font-size: 11px; fill: #e6edf3; pointer-events: none;
               text-shadow: 0 1px 3px #0d1117; }
  .link { stroke: #30363d; stroke-opacity: 0.6; }
  .link.llamó     { stroke: #e05252; }
  .link.ordenó    { stroke: #ff6b35; }
  .link.coordinó  { stroke: #4a90d9; }
  .link.apoyó     { stroke: #38c77e; }
  .link.se_opuso        { stroke: #8b949e; stroke-dasharray: 4; }
  .link.informó         { stroke: #c084fc; }
  .link.juzgó           { stroke: #fb923c; }
  .link.member_of       { stroke: #475569; stroke-opacity: 0.4; }
  .link.mentioned_in    { stroke: #38bdf8; stroke-opacity: 0.35; }
  .link.documents_event { stroke: #34d399; stroke-opacity: 0.35; }
  .dimmed { opacity: 0.1 !important; }

  /* ── Detail panel ── */
  #detail { width: 340px; background: #161b22; border-left: 1px solid #30363d;
             overflow-y: auto; flex-shrink: 0; position: relative; }
  #detail-close { position: absolute; top: 8px; right: 8px;
                   background: #21262d; border: 1px solid #30363d; color: #8b949e;
                   width: 26px; height: 26px; border-radius: 50%; cursor: pointer;
                   font-size: 14px; line-height: 26px; text-align: center;
                   z-index: 10; transition: color .15s, border-color .15s; }
  #detail-close:hover { color: #e6edf3; border-color: #e6edf3; }
  .detail-placeholder { padding: 40px 20px; color: #8b949e; text-align: center;
                         font-size: 13px; line-height: 1.6; }
  .detail-placeholder h3 { color: #e6edf3; margin-bottom: 8px; }
  .detail-content { padding: 16px; }
  .detail-type-badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
                        font-size: 11px; font-weight: 600; margin-bottom: 10px; }
  .detail-title { font-size: 15px; font-weight: 700; line-height: 1.4; margin-bottom: 6px; }
  .detail-subtitle { font-size: 12px; color: #8b949e; margin-bottom: 12px; }
  .detail-section { margin-bottom: 14px; }
  .detail-section h4 { font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
                         color: #8b949e; margin-bottom: 6px; border-bottom: 1px solid #30363d;
                         padding-bottom: 4px; }
  .detail-section p { font-size: 13px; line-height: 1.6; color: #c9d1d9; }
  .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px;
          background: #21262d; color: #8b949e; margin: 2px 2px 2px 0; }
  .quote-block { background: #21262d; border-left: 3px solid #f0b429; padding: 8px 12px;
                  margin: 6px 0; border-radius: 0 4px 4px 0; }
  .quote-block p { font-size: 12px; font-style: italic; color: #e6edf3; }
  .quote-block small { font-size: 11px; color: #8b949e; }
  .open-pdf { display: block; margin-top: 12px; padding: 8px; text-align: center;
               background: #21262d; border: 1px solid #30363d; border-radius: 6px;
               color: #58a6ff; text-decoration: none; font-size: 12px; }
  .open-pdf:hover { background: #30363d; }

  /* ── Timeline ── */
  #timeline-wrapper { flex-shrink: 0; display: flex; flex-direction: column; height: 122px; }
  #timeline-resize-handle { height: 6px; cursor: ns-resize; background: #0d1117;
                             flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
  #timeline-resize-handle::after { content: ''; display: block; width: 36px; height: 3px;
                                    border-radius: 2px; background: #30363d; transition: background .15s, width .15s; }
  #timeline-resize-handle:hover::after, #timeline-resize-handle.dragging::after { background: #f0b429; width: 52px; }
  #period-tabs { padding: 5px 20px; background: #161b22; border-top: 1px solid #30363d;
                 display: flex; gap: 6px; align-items: center; flex-shrink: 0; }
  .period-tab-label { font-size: 11px; color: #8b949e; margin-right: 4px; }
  .period-tab { padding: 3px 10px; border-radius: 12px; border: 1px solid #30363d;
                background: #21262d; color: #8b949e; cursor: pointer; font-size: 11px;
                font-weight: 600; transition: all .15s; }
  .period-tab[data-period="pre-golpe"].active  { background: #f0b429; color: #0d1117; border-color: transparent; }
  .period-tab[data-period="golpe"].active      { background: #e05252; color: #fff;    border-color: transparent; }
  .period-tab[data-period="post-golpe"].active { background: #4a90d9; color: #fff;    border-color: transparent; }
  .period-tab[data-period="juicio"].active     { background: #38c77e; color: #0d1117; border-color: transparent; }
  #timeline { flex: 1; min-height: 0; background: #161b22; border-top: 1px solid #30363d;
               position: relative; overflow: hidden; }
  #timeline-svg { width: 100%; height: 100%; }
  .tl-event circle { cursor: pointer; }
  .tl-axis text { fill: #8b949e; font-size: 10px; }
  .tl-axis line, .tl-axis path { stroke: #30363d; }

  /* ── Stats bar ── */
  .stats { padding: 4px 20px; background: #0d1117; border-top: 1px solid #30363d;
            font-size: 11px; color: #8b949e; display: flex; gap: 16px; flex-shrink: 0; }
</style>
</head>
<body>

<header>
  <div>
    <h1>⚖️ 23-F — Golpe de Estado 1981</h1>
    <span>Documentos desclasificados · Declassified documents · Feb 25, 2026</span>
  </div>
  <div class="lang-toggle">
    <button id="btn-es" class="active" onclick="setLang('es')">ES</button>
    <button id="btn-en" onclick="setLang('en')">EN</button>
  </div>
</header>

<div class="filters">
  <label id="label-show">Mostrar:</label>
  <button class="filter-btn person active" onclick="toggleType('person')">● Personas</button>
  <button class="filter-btn organization active" onclick="toggleType('organization')">■ Organizaciones</button>
  <button class="filter-btn event active" onclick="toggleType('event')">◆ Eventos</button>
  <button class="filter-btn document active" onclick="toggleType('document')">▶ Documentos</button>
  <input class="search-box" id="search" type="text" placeholder="Buscar / Search…" oninput="filterSearch(this.value)">
</div>

<div class="main">
  <div id="graph-container">
    <svg id="graph"></svg>
    <button id="zoom-reset" onclick="resetZoom()" title="Reset view / Vista inicial" style="position:absolute;top:10px;right:10px;background:#21262d;border:1px solid #30363d;color:#e6edf3;padding:6px 10px;border-radius:6px;cursor:pointer;font-size:13px;z-index:10">&#8857; Reset</button>
  </div>
  <div id="detail">
    <div class="detail-placeholder">
      <h3>23-F Knowledge Map</h3>
      <p>Haz clic en cualquier nodo para ver los detalles del documento, persona u organización.</p>
      <p style="margin-top:8px">Click any node to explore details.</p>
      <p style="margin-top:20px; font-size:11px">
        <span style="color:#e05252">●</span> Personas &nbsp;
        <span style="color:#4a90d9">■</span> Organizaciones &nbsp;
        <span style="color:#f0b429">◆</span> Eventos &nbsp;
        <span style="color:#38c77e">▶</span> Documentos
      </p>
    </div>
  </div>
</div>

<div id="timeline-wrapper">
  <div id="timeline-resize-handle" title="Drag to resize / Arrastra para redimensionar"></div>
  <div id="period-tabs">
    <span class="period-tab-label" id="tl-label">Periodo:</span>
    <button class="period-tab active" data-period="pre-golpe" onclick="selectPeriod('pre-golpe')">Pre-golpe</button>
    <button class="period-tab" data-period="golpe" onclick="selectPeriod('golpe')">23-F</button>
    <button class="period-tab" data-period="post-golpe" onclick="selectPeriod('post-golpe')">Post-golpe</button>
    <button class="period-tab" data-period="juicio" onclick="selectPeriod('juicio')">Juicio</button>
  </div>
  <div id="timeline"><svg id="timeline-svg"></svg></div>
</div>

<div class="stats" id="stats-bar">
  Cargando / Loading…
</div>

<script>
// ── Data (injected by build_viz.py) ──────────────────────────────────────────
const GRAPH_DATA = __GRAPH_DATA__;
const TIMELINE_DATA = __TIMELINE_DATA__;
const PDF_BASE = "__PDF_BASE__";

// ── Security: HTML-escape helper (C-3, H-2) ───────────────────────────────────
function esc(s) {
  if (s == null) return '';
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

// ── State ─────────────────────────────────────────────────────────────────────
let currentLang = 'es';
let activeTypes = new Set(['person', 'organization', 'event', 'document']);
let selectedNode = null;
let simulation, svgEl, linkEl, nodeEl, zoomBehavior;

// ── Language helper ───────────────────────────────────────────────────────────
function t(node, esKey, enKey) {
  return currentLang === 'es' ? (node[esKey] || node[enKey] || '') : (node[enKey] || node[esKey] || '');
}

function setLang(lang) {
  currentLang = lang;
  document.getElementById('btn-es').classList.toggle('active', lang === 'es');
  document.getElementById('btn-en').classList.toggle('active', lang === 'en');
  document.getElementById('label-show').textContent = lang === 'es' ? 'Mostrar:' : 'Show:';
  const labels = {
    person:       { es: '● Personas',       en: '● Persons' },
    organization: { es: '■ Organizaciones', en: '■ Organizations' },
    event:        { es: '◆ Eventos',        en: '◆ Events' },
    document:     { es: '▶ Documentos',     en: '▶ Documents' },
  };
  document.querySelectorAll('.filter-btn').forEach(btn => {
    const type = ['person','organization','event','document'].find(t => btn.classList.contains(t));
    if (type) btn.textContent = labels[type][lang];
  });
  const periodLabels = {
    'pre-golpe': { es: 'Pre-golpe', en: 'Pre-coup' },
    'golpe':     { es: '23-F',      en: '23-F' },
    'post-golpe':{ es: 'Post-golpe',en: 'Post-coup' },
    'juicio':    { es: 'Juicio',    en: 'Trial' },
  };
  document.querySelectorAll('.period-tab').forEach(b => {
    const pid = b.dataset.period;
    if (periodLabels[pid]) b.textContent = periodLabels[pid][lang];
  });
  document.getElementById('tl-label').textContent = lang === 'es' ? 'Periodo:' : 'Period:';
  d3.select('#timeline-svg').selectAll('*').remove();
  initTimeline();
  updateStats();
  if (selectedNode) showDetail(selectedNode);
}

// ── Filter helpers ────────────────────────────────────────────────────────────
function toggleType(type) {
  if (activeTypes.has(type) && activeTypes.size === 1) return; // keep at least one type active
  if (activeTypes.has(type)) activeTypes.delete(type);
  else activeTypes.add(type);
  document.querySelectorAll(`.filter-btn.${type}`).forEach(b =>
    b.classList.toggle('active', activeTypes.has(type)));
  applyFilters();
}

function panToNode(d) {
  if (d.x == null || d.y == null) return;
  const c = document.getElementById('graph-container');
  const W = c.clientWidth, H = c.clientHeight;
  const k = d3.zoomTransform(svgEl.node()).k; // keep current scale
  svgEl.transition().duration(600).call(
    zoomBehavior.transform,
    d3.zoomIdentity.translate(W / 2 - k * d.x, H / 2 - k * d.y).scale(k)
  );
}

function filterSearch(query) {
  const q = query.toLowerCase().trim();
  if (q.length < 2) {
    nodeEl.classed('dimmed', false);
    document.getElementById('search-hint')?.remove();
    return;
  }
  const normalize = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const nq = normalize(q);
  const matches = GRAPH_DATA.nodes.filter(d => normalize(d.label).includes(nq));
  nodeEl.classed('dimmed', d => !normalize(d.label).includes(nq));

  // Remove old hint
  document.getElementById('search-hint')?.remove();
  const hint = document.createElement('div');
  hint.id = 'search-hint';
  hint.style.cssText = 'position:absolute;top:40px;right:20px;font-size:11px;padding:4px 8px;border-radius:4px;z-index:20;';
  if (matches.length === 0) {
    hint.style.background = '#3d1a1a'; hint.style.color = '#e05252';
    hint.textContent = 'Sin resultados / No results';
  } else {
    hint.style.background = '#1a2d1a'; hint.style.color = '#38c77e';
    hint.textContent = `${matches.length} resultado${matches.length > 1 ? 's' : ''}`;
  }
  if (matches.length === 1) {
    showDetail(matches[0]);   // showDetail removes search-hint internally
    panToNode(matches[0]);
  }
  // Append hint last so showDetail's removal doesn't swallow it
  document.getElementById('graph-container').appendChild(hint);
}

function applyFilters() {
  nodeEl.style('display', d => activeTypes.has(d.type) ? null : 'none');
  linkEl.style('display', l => {
    const srcVisible = activeTypes.has(GRAPH_DATA.nodes.find(n => n.id === l.source.id)?.type);
    const tgtVisible = activeTypes.has(GRAPH_DATA.nodes.find(n => n.id === l.target.id)?.type);
    return srcVisible && tgtVisible ? null : 'none';
  });
}

// ── Stats bar ─────────────────────────────────────────────────────────────────
function updateStats() {
  const n = GRAPH_DATA.nodes, e = GRAPH_DATA.edges, l = currentLang;
  const w = l === 'es'
    ? { nodes:'Nodos', edges:'Conexiones', persons:'Personas', docs:'Documentos', orgs:'Organizaciones', events:'Eventos' }
    : { nodes:'Nodes', edges:'Connections', persons:'Persons', docs:'Documents', orgs:'Organizations', events:'Events' };
  document.getElementById('stats-bar').textContent =
    `${w.nodes}: ${n.length}  |  ${w.edges}: ${e.length}  |  ` +
    `${w.persons}: ${n.filter(x=>x.type==='person').length}  |  ` +
    `${w.docs}: ${n.filter(x=>x.type==='document').length}  |  ` +
    `${w.orgs}: ${n.filter(x=>x.type==='organization').length}  |  ` +
    `${w.events}: ${n.filter(x=>x.type==='event').length}`;
}

// ── D3 Graph ──────────────────────────────────────────────────────────────────
function initGraph() {
  const container = document.getElementById('graph-container');
  const W = container.clientWidth;
  const H = container.clientHeight;

  zoomBehavior = d3.zoom().scaleExtent([0.2, 4]).on('zoom', e => g.attr('transform', e.transform));
  svgEl = d3.select('#graph')
    .attr('viewBox', [0, 0, W, H])
    .call(zoomBehavior);

  // Arrow markers (defs must come before g so markers are defined in DOM first)
  svgEl.append('defs').selectAll('marker')
    .data(['default'])
    .join('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 18).attr('refY', 0)
      .attr('markerWidth', 6).attr('markerHeight', 6)
      .attr('orient', 'auto')
    .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#30363d');

  const g = svgEl.append('g');

  // Links
  linkEl = g.append('g').selectAll('line')
    .data(GRAPH_DATA.edges)
    .join('line')
      .attr('class', d => `link ${d.type}`)
      .attr('stroke-width', 1.2)
      .attr('marker-end', 'url(#arrow)');

  // Nodes
  const nodeGroups = g.append('g').selectAll('.node')
    .data(GRAPH_DATA.nodes)
    .join('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragStart)
        .on('drag',  dragged)
        .on('end',   dragEnd))
      .on('click', (event, d) => { event.stopPropagation(); showDetail(d); });

  nodeEl = nodeGroups;

  nodeGroups.append('circle')
    .attr('r', d => d.size)
    .attr('fill', d => d.color);

  nodeGroups.append('text')
    .attr('dy', d => d.size + 12)
    .attr('text-anchor', 'middle')
    .style('opacity', d => d.size >= 14 ? 1 : 0.5)
    .text(d => d.label.length > 20 ? d.label.slice(0, 18) + '…' : d.label);

  // Clear selection on background click
  svgEl.on('click', () => { clearDetail(); selectedNode = null; });

  // Force simulation
  simulation = d3.forceSimulation(GRAPH_DATA.nodes)
    .force('link', d3.forceLink(GRAPH_DATA.edges).id(d => d.id).distance(120))
    .force('charge', d3.forceManyBody().strength(-280))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('collision', d3.forceCollide().radius(d => d.size + 22))
    .on('tick', ticked);

  function ticked() {
    linkEl
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    nodeGroups.attr('transform', d => `translate(${d.x},${d.y})`);
  }

  function dragStart(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
  }
  function dragged(event, d) { d.fx = event.x; d.fy = event.y; }
  function dragEnd(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null; d.fy = null;
  }

  // Stats
  updateStats();
}

function resetZoom() {
  // 1. Reset pan/zoom
  svgEl.transition().duration(500).call(zoomBehavior.transform, d3.zoomIdentity);

  // 2. Clear selected node and detail panel
  clearDetail();
  selectedNode = null;

  // 3. Re-enable all node type filters
  activeTypes = new Set(['person', 'organization', 'event', 'document']);
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.add('active'));
  applyFilters();

  // 4. Clear search box and remove dimming/hint
  const searchBox = document.getElementById('search');
  if (searchBox) searchBox.value = '';
  nodeEl && nodeEl.classed('dimmed', false);
  document.getElementById('search-hint')?.remove();

  // 5. Reheat simulation so nodes spread back out
  simulation && simulation.alpha(0.3).restart();
}

// ── Detail panel ──────────────────────────────────────────────────────────────
const TYPE_LABELS = {
  person: { es: 'Persona', en: 'Person', color: '#e05252' },
  organization: { es: 'Organización', en: 'Organization', color: '#4a90d9' },
  event: { es: 'Evento', en: 'Event', color: '#f0b429' },
  document: { es: 'Documento', en: 'Document', color: '#38c77e' },
};

function showDetail(d) {
  document.getElementById('search-hint')?.remove();
  selectedNode = d;
  const panel = document.getElementById('detail');
  const tl = TYPE_LABELS[d.type] || { es: d.type, en: d.type, color: '#8b949e' };
  const lang = currentLang;

  // C-3: all user-data interpolations use esc() — never raw innerHTML
  let html = `<div class="detail-content">`;
  html += `<span class="detail-type-badge" style="background:${esc(tl.color)};color:${d.type==='event'||d.type==='document'?'#000':'#fff'}">${esc(tl[lang])}</span>`;
  html += `<div class="detail-title">${esc(d.label)}</div>`;

  if (d.type === 'document') {
    const subtitle = lang === 'es' ? d.titulo_es : d.titulo_en;
    if (subtitle && subtitle !== d.label)
      html += `<div class="detail-subtitle">${esc(subtitle)}</div>`;

    if (d.fecha) html += `<div class="detail-subtitle">📅 ${esc(d.fecha)}${d.clasificacion ? ` &nbsp;·&nbsp; 🔒 ${esc(d.clasificacion)}` : ''}</div>`;
    if (d.ministerio) html += `<div class="detail-subtitle">🏛 ${esc(d.ministerio)} &nbsp;·&nbsp; ${esc(d.tipo||'')}</div>`;

    const resumen = lang === 'es' ? d.resumen_es : d.resumen_en;
    if (resumen) {
      html += `<div class="detail-section"><h4>${lang==='es'?'Resumen':'Summary'}</h4><p>${esc(resumen)}</p></div>`;
    }

    if (d.citas && d.citas.length) {
      html += `<div class="detail-section"><h4>${lang==='es'?'Citas clave':'Key quotes'}</h4>`;
      d.citas.slice(0,3).forEach(q => {
        // JSON schema uses texto_es/texto_en/fuente (not texto/autor)
        const texto = lang === 'es' ? (q.texto_es || q.texto) : (q.texto_en || q.traduccion_en || q.texto_es || q.texto);
        const fuente = q.fuente || q.autor || 'Desconocido';
        html += `<div class="quote-block"><p>"${esc(texto)}"</p><small>— ${esc(fuente)}</small></div>`;
      });
      html += `</div>`;
    }

    if (d.temas && d.temas.length)
      html += `<div class="detail-section"><h4>Temas / Topics</h4>${d.temas.map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div>`;

    if (d.folder && d.filename) {
      const pdfPath = PDF_BASE + d.folder + '/' + d.filename;
      html += `<a class="open-pdf" href="${esc(pdfPath)}" target="_blank" rel="noopener noreferrer">📄 ${lang==='es'?'Abrir PDF original':'Open original PDF'}</a>`;
    }
  }

  else if (d.type === 'person') {
    if (d.cargo) html += `<div class="detail-subtitle">🎖 ${esc(d.cargo)}</div>`;
    if (d.org)   html += `<div class="detail-subtitle">🏛 ${esc(d.org)}</div>`;
    // Birth/death dates if available from enriched profile
    if (d.fecha_nac) {
      const lifespan = d.fecha_def ? `${esc(d.fecha_nac)} – ${esc(d.fecha_def)}` : `n. ${esc(d.fecha_nac)}`;
      html += `<div class="detail-subtitle">📆 ${lifespan}</div>`;
    }
    if (d.rol_23f) {
      const rolColors = { conspirador:'#e05252', leal:'#38c77e', neutral:'#8b949e', víctima:'#f0b429', testigo:'#4a90d9' };
      html += `<span class="detail-type-badge" style="background:${esc(rolColors[d.rol_23f]||'#8b949e')};color:#fff">${esc(d.rol_23f)}</span>`;
    }
    // Enriched biographical description
    const desc = lang === 'es' ? d.descripcion_es : d.descripcion_en;
    if (desc) html += `<div class="detail-section"><h4>${lang==='es'?'Biografía':'Biography'}</h4><p>${esc(desc)}</p></div>`;
    // Key actions during 23-F
    if (d.acciones_23f && d.acciones_23f.length) {
      html += `<div class="detail-section"><h4>${lang==='es'?'Acciones el 23-F':'Actions on 23-F'}</h4><ul style="padding-left:16px;margin:0">`;
      d.acciones_23f.forEach(a => { html += `<li style="font-size:12px;color:#c9d1d9;margin-bottom:4px">${esc(typeof a === 'object' ? (lang==='es'?a.es:a.en)||a.es : a)}</li>`; });
      html += `</ul></div>`;
    }
    // Trial sentence
    if (d.condena) html += `<div class="detail-section"><h4>${lang==='es'?'Condena':'Sentence'}</h4><p style="color:#f0b429">${esc(d.condena)}</p></div>`;
    // Wikipedia links
    if (d.wikipedia_es || d.wikipedia_en) {
      html += `<div class="detail-section"><h4>Wikipedia</h4>`;
      if (d.wikipedia_es) html += `<a href="${esc(d.wikipedia_es)}" target="_blank" rel="noopener noreferrer" style="display:block;font-size:12px;color:#58a6ff;margin-bottom:4px">🔗 ES</a>`;
      if (d.wikipedia_en) html += `<a href="${esc(d.wikipedia_en)}" target="_blank" rel="noopener noreferrer" style="display:block;font-size:12px;color:#58a6ff">🔗 EN</a>`;
      html += `</div>`;
    }
    const connectedNodes = GRAPH_DATA.edges
      .filter(e => (e.source.id||e.source) === d.id || (e.target.id||e.target) === d.id)
      .map(e => (e.source.id||e.source) === d.id ? (e.target.id||e.target) : (e.source.id||e.source))
      .map(nid => GRAPH_DATA.nodes.find(n => n.id === nid))
      .filter(Boolean);
    if (connectedNodes.length) {
      html += `<div class="detail-section"><h4>${lang==='es'?'Conexiones':'Connections'} (${connectedNodes.length})</h4>`;
      // C-2: use data-node-id attribute instead of onclick interpolation
      connectedNodes.slice(0, 8).forEach(cn => {
        html += `<span class="tag" style="cursor:pointer;border:1px solid ${esc(cn.color)};color:${esc(cn.color)}" data-node-id="${esc(cn.id)}">${esc(cn.label.slice(0,30))}</span>`;
      });
      html += '</div>';
    }
  }

  else if (d.type === 'event') {
    if (d.fecha) html += `<div class="detail-subtitle">📅 ${esc(d.fecha)}</div>`;
    if (d.lugar) html += `<div class="detail-subtitle">📍 ${esc(d.lugar)}</div>`;
    const desc = lang === 'es' ? d.desc_es : d.desc_en;
    if (desc) html += `<div class="detail-section"><h4>${lang==='es'?'Descripción':'Description'}</h4><p>${esc(desc)}</p></div>`;
  }

  else if (d.type === 'organization') {
    if (d.tipo_org) html += `<div class="detail-subtitle">${esc(d.tipo_org)}</div>`;
    const connectedNodes = GRAPH_DATA.edges
      .filter(e => (e.source.id||e.source) === d.id || (e.target.id||e.target) === d.id)
      .map(e => (e.source.id||e.source) === d.id ? (e.target.id||e.target) : (e.source.id||e.source))
      .map(nid => GRAPH_DATA.nodes.find(n => n.id === nid))
      .filter(Boolean);
    if (connectedNodes.length) {
      html += `<div class="detail-section"><h4>${lang==='es'?'Conexiones':'Connections'} (${connectedNodes.length})</h4>`;
      // C-2: use data-node-id attribute instead of onclick interpolation
      connectedNodes.slice(0, 8).forEach(cn => {
        html += `<span class="tag" style="cursor:pointer;border:1px solid ${esc(cn.color)};color:${esc(cn.color)}" data-node-id="${esc(cn.id)}">${esc(cn.label.slice(0,30))}</span>`;
      });
      html += '</div>';
    }
  }

  html += `</div>`;
  panel.innerHTML = html;

  // C-2: Close button created via DOM API (no onclick injection in innerHTML)
  const closeBtn = document.createElement('button');
  closeBtn.id = 'detail-close';
  closeBtn.title = 'Cerrar / Close';
  closeBtn.textContent = '×';
  closeBtn.addEventListener('click', e => { e.stopPropagation(); clearDetail(); selectedNode = null; });
  panel.insertBefore(closeBtn, panel.firstChild);

  // Highlight connected nodes
  const connectedIds = new Set([d.id]);
  GRAPH_DATA.edges.forEach(e => {
    if ((e.source.id || e.source) === d.id) connectedIds.add(e.target.id || e.target);
    if ((e.target.id || e.target) === d.id) connectedIds.add(e.source.id || e.source);
  });
  nodeEl.classed('dimmed', n => !connectedIds.has(n.id));
  linkEl.classed('dimmed', l =>
    (l.source.id||l.source) !== d.id && (l.target.id||l.target) !== d.id);
}

function clearDetail() {
  const msg = currentLang === 'es'
    ? 'Haz clic en cualquier nodo para ver detalles.'
    : 'Click any node to explore details.';
  document.getElementById('detail').innerHTML = `
    <div class="detail-placeholder">
      <h3>23-F Knowledge Map</h3>
      <p>${msg}</p>
      <p style="margin-top:8px; font-size:11px">
        <span style="color:#e05252">●</span> ${currentLang==='es'?'Personas':'Persons'} &nbsp;
        <span style="color:#4a90d9">■</span> ${currentLang==='es'?'Organizaciones':'Organizations'} &nbsp;
        <span style="color:#f0b429">◆</span> ${currentLang==='es'?'Eventos':'Events'} &nbsp;
        <span style="color:#38c77e">▶</span> ${currentLang==='es'?'Documentos':'Documents'}
      </p>
    </div>`;
  nodeEl && nodeEl.classed('dimmed', false);
  linkEl && linkEl.classed('dimmed', false);
}

// ── Timeline ──────────────────────────────────────────────────────────────────
const PERIOD_DEFS = [
  { id: 'pre-golpe',  start: '1977-01-01',      end: '1981-02-22',
    label_es: 'Pre-golpe',         label_en: 'Pre-coup',       color: '#f0b429', fmt: '%b %Y',  ticks: 8 },
  { id: 'golpe',      start: '1981-02-23T00:00', end: '1981-02-23T23:59',
    label_es: '23 Feb 1981',       label_en: 'Feb 23, 1981',   color: '#e05252', fmt: '%H:%M',  ticks: 12, hourly: true },
  { id: 'post-golpe', start: '1981-02-24',       end: '1982-07-01',
    label_es: 'Post-golpe',        label_en: 'Post-coup',      color: '#4a90d9', fmt: '%b %Y',  ticks: 8 },
  { id: 'juicio',     start: '1982-07-01',       end: '1984-01-01',
    label_es: 'Juicio',            label_en: 'Trial',          color: '#38c77e', fmt: '%b %Y',  ticks: 6 },
];
let activePeriod = 'pre-golpe';

function selectPeriod(pid) {
  activePeriod = pid;
  document.querySelectorAll('.period-tab').forEach(b =>
    b.classList.toggle('active', b.dataset.period === pid));
  d3.select('#timeline-svg').selectAll('*').remove();
  initTimeline();
}

function initTimeline() {
  const def = PERIOD_DEFS.find(p => p.id === activePeriod);
  const svg = d3.select('#timeline-svg');
  svg.selectAll('*').remove();

  const tlEl = document.getElementById('timeline');
  const W = tlEl.clientWidth;
  const H = tlEl.clientHeight || 80;
  const margin = { left: 50, right: 20, top: 14, bottom: 26 };

  // Filter events first so we can derive the axis domain from actual data
  const periodEvents = TIMELINE_DATA.filter(d => {
    if (!d.date || !d.date.match(/^\d{4}/)) return false;
    const dp = d.period || 'pre-golpe';
    if (activePeriod === 'golpe')
      return dp === 'golpe' || d.date.startsWith('1981-02-23');
    return dp === activePeriod;
  });

  // Derive axis domain from actual data extent, with padding
  let [dMin, dMax] = d3.extent(periodEvents, d => new Date(d.date));
  if (!dMin) { dMin = new Date(def.start); dMax = new Date(def.end); }
  const span = dMax - dMin || 1;
  // Pad: 4% of span, minimum 30 min for golpe period, 1 day for others
  const minPad = def.hourly ? 30 * 60 * 1000 : 24 * 60 * 60 * 1000;
  const pad = Math.max(span * 0.04, minPad);
  dMin = new Date(+dMin - pad);
  dMax = new Date(+dMax + pad);

  const x = d3.scaleTime()
    .domain([dMin, dMax])
    .range([margin.left, W - margin.right]);

  // Axis
  svg.append('g')
    .attr('class', 'tl-axis')
    .attr('transform', `translate(0,${H - margin.bottom})`)
    .call(d3.axisBottom(x).ticks(def.ticks).tickFormat(d3.timeFormat(def.fmt)));

  // Period label
  svg.append('text')
    .attr('x', margin.left).attr('y', margin.top)
    .attr('fill', def.color).attr('font-size', '10px').attr('font-weight', '700')
    .text(currentLang === 'es' ? def.label_es : def.label_en);

  if (!periodEvents.length) {
    svg.append('text')
      .attr('x', W / 2).attr('y', H / 2)
      .attr('text-anchor', 'middle').attr('fill', '#8b949e').attr('font-size', '12px')
      .text(currentLang === 'es' ? 'Sin datos para este periodo' : 'No data for this period');
    return;
  }

  const DOT_R  = 5;
  const centerY = margin.top + (H - margin.top - margin.bottom) / 2;
  const periodColor = { 'pre-golpe':'#f0b429','golpe':'#e05252','post-golpe':'#4a90d9','juicio':'#38c77e','otro':'#8b949e' };

  // Compute clamped x position for each event
  const getX = d => {
    const dt = new Date(d.date);
    return isNaN(dt.getTime()) ? margin.left
         : Math.max(margin.left, Math.min(W - margin.right, x(dt)));
  };

  // Beeswarm: fix x to time position, let y spread via force collision
  const simNodes = periodEvents.map(d => ({ d, fx: getX(d), y: centerY }));
  d3.forceSimulation(simNodes)
    .force('y', d3.forceY(centerY).strength(0.08))
    .force('collide', d3.forceCollide(DOT_R + 2).strength(1))
    .stop()
    .tick(200);

  const yMin = margin.top + DOT_R;
  const yMax = H - margin.bottom - DOT_R;

  svg.selectAll('.tl-event')
    .data(simNodes)
    .join('g')
      .attr('class', 'tl-event')
      .attr('transform', n => `translate(${n.fx},${Math.max(yMin, Math.min(yMax, n.y))})`)
    .call(g => g.append('circle')
      .attr('r', DOT_R)
      .attr('fill', n => periodColor[n.d.period] || '#8b949e')
      .attr('opacity', 0.85)
      .style('cursor', 'pointer')
      .on('mouseover', (event, n) => showTimelineTooltip(event, n.d))
      .on('mouseout', hideTooltip)
      .on('click', (event, n) => {
        if (n.d.doc_id) {
          const node = GRAPH_DATA.nodes.find(nd => nd.doc_id === n.d.doc_id);
          if (node) showDetail(node);
        }
      })
    );
}

let tooltip;
function showTimelineTooltip(event, d) {
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.style.cssText = 'position:fixed;background:#21262d;border:1px solid #30363d;padding:6px 10px;border-radius:6px;font-size:11px;color:#e6edf3;pointer-events:none;z-index:99;max-width:200px';
    document.body.appendChild(tooltip);
  }
  // H-2: use esc() — never raw innerHTML with data values
  tooltip.innerHTML = `<strong>${esc(d.date)}</strong><br>${esc(currentLang==='es'?d.title:d.title_en||d.title)}`;
  tooltip.style.display = 'block';
  // Flip to the left when near the right edge of the viewport
  const gap = 10;
  const ttW = tooltip.offsetWidth;
  const overflows = event.clientX + gap + ttW > window.innerWidth;
  tooltip.style.left = overflows
    ? (event.clientX - gap - ttW) + 'px'
    : (event.clientX + gap) + 'px';
  tooltip.style.top = (event.clientY - 30) + 'px';
}
function hideTooltip() { if (tooltip) tooltip.style.display = 'none'; }

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  initGraph();
  initTimeline();

  // C-2: event delegation for data-node-id connection tags in detail panel
  document.getElementById('detail').addEventListener('click', e => {
    const tag = e.target.closest('[data-node-id]');
    if (tag) {
      e.stopPropagation();
      const node = GRAPH_DATA.nodes.find(n => n.id === tag.dataset.nodeId);
      if (node) showDetail(node);
    }
  });

  // ── Timeline resize handle ─────────────────────────────────────────────────
  let tlResizing = false, tlStartY = 0, tlStartH = 0;
  const tlHandle  = document.getElementById('timeline-resize-handle');
  const tlWrapper = document.getElementById('timeline-wrapper');

  tlHandle.addEventListener('mousedown', e => {
    tlResizing = true;
    tlStartY   = e.clientY;
    tlStartH   = tlWrapper.offsetHeight;
    tlHandle.classList.add('dragging');
    document.body.style.cursor     = 'ns-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });
  document.addEventListener('mousemove', e => {
    if (!tlResizing) return;
    const delta = tlStartY - e.clientY;          // drag up → positive delta → taller
    const newH  = Math.max(60, Math.min(500, tlStartH + delta));
    tlWrapper.style.height = newH + 'px';
    d3.select('#timeline-svg').selectAll('*').remove();
    initTimeline();
  });
  document.addEventListener('mouseup', () => {
    if (!tlResizing) return;
    tlResizing = false;
    tlHandle.classList.remove('dragging');
    document.body.style.cursor     = '';
    document.body.style.userSelect = '';
  });
});
window.addEventListener('resize', () => {
  const c = document.getElementById('graph-container');
  const W = c.clientWidth, H = c.clientHeight;
  svgEl && svgEl.attr('viewBox', [0, 0, W, H]);
  simulation && simulation.force('center', d3.forceCenter(W/2, H/2)).alpha(0.1).restart();
  d3.select('#timeline-svg').selectAll('*').remove();
  initTimeline();
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    const searchBox = document.getElementById('search');
    if (searchBox.value) {
      searchBox.value = '';
      filterSearch('');
    }
    clearDetail();
    selectedNode = null;
  }
});
</script>
</body>
</html>
"""

def generate_html(graph: dict, timeline: list) -> str:
    graph_json    = json.dumps(graph,    ensure_ascii=False, separators=(',', ':'))
    timeline_json = json.dumps(timeline, ensure_ascii=False, separators=(',', ':'))

    # H-3: prevent </script> injection when JSON is embedded inside <script> tags
    graph_json    = graph_json.replace('</', '<\\/')
    timeline_json = timeline_json.replace('</', '<\\/')

    # C-1: PDF base URL from env var; fall back to local dev path with a warning
    pdf_base = os.environ.get('PDF_BASE_URL', '').rstrip('/')
    if pdf_base:
        if not pdf_base.startswith('https://'):
            raise ValueError(
                f"PDF_BASE_URL must start with https:// (got: {pdf_base!r}). "
                "Refusing to embed non-https URL in published HTML."
            )
        pdf_base += '/'
    else:
        pdf_base = 'file:///Users/ricardodelarrearemiro/Downloads/23F/'
        print("⚠  PDF_BASE_URL not set — using local file path (development only).")
        print("   Set PDF_BASE_URL=https://your-bucket/path/ before publishing.")

    html_out = HTML_TEMPLATE.replace("__PDF_BASE__", pdf_base)
    html_out = html_out.replace("__GRAPH_DATA__",    graph_json)
    html_out = html_out.replace("__TIMELINE_DATA__", timeline_json)
    return html_out

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    ensure_d3()  # H-1: vendor D3 before building HTML

    docs = load_docs()
    if not docs:
        print("❌  No extracted documents found in data/. Run extract.py first.")
        return

    print(f"📂  Loaded {len(docs)} extracted documents")

    profiles = load_profiles()
    graph    = build_graph(docs, profiles)
    timeline = build_timeline(docs)

    print(f"🕸   Graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges")
    print(f"📅  Timeline: {len(timeline)} events")

    html = generate_html(graph, timeline)
    OUTPUT.write_text(html, encoding="utf-8")

    print(f"\n✅  Visualization saved to: {OUTPUT}")
    print(f"   Open in browser: open {OUTPUT}")

if __name__ == "__main__":
    main()
