# 23-F Explorer

Interactive knowledge graph and timeline of the 23-F coup attempt (Spain, 1981).
Built from declassified documents: people, organisations, and events linked by role.

## Build

```bash
python3 build_viz.py
# → produces index.html (self-contained, embeds D3 from vendor/)
```

Optional — enable PDF buttons:

```bash
PDF_BASE_URL=https://your-host/pdfs/ python3 build_viz.py
```

`PDF_BASE_URL` must start with `https://`. When unset, the PDF button is hidden.

## Deploy (SiteGround Git integration)

1. Connect this repo to SiteGround via **Git** in Site Tools.
2. SiteGround pulls `main` automatically on every push.
3. Upload the PDF archive once directly to SiteGround (too large for git).
4. Set `PDF_BASE_URL` to the public URL of that upload, rebuild, commit, and push.

```bash
PDF_BASE_URL=https://example.com/23f-pdfs/ python3 build_viz.py
git add index.html
git commit -m "Rebuild with PDF links"
git push
```

## Data

Source JSON files live in `data/`. Person profiles are in `data/profiles/`.
D3 is vendored in `vendor/d3.min.js` to avoid CDN dependency.
