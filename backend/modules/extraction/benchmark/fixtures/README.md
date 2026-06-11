# Benchmark fixtures — Sprint 0 (issue #3)

The benchmark needs **15 PII-scrubbed** contract images (lease / supplier / labor,
F&B–bán lẻ seed) plus ground-truth field values.

## ⚠️ PII rule (NĐ 13/2023)

- **Never commit real PII.** Scrub names, tax codes, addresses, phone numbers,
  signatures, and stamps before adding any image. Replace with synthetic
  equivalents (e.g. "Công ty TNHH ABC", "Ông Nguyễn Văn X").
- The `data/` directory is **gitignored** — sample images stay local / on the
  benchmark box. Only the manifest schema + this README are committed.

## How to run

1. Copy `manifest.example.json` → `manifest.json`.
2. Put the 15 scrubbed images in `data/` (paths are relative to the manifest).
3. Fill each sample's `ground_truth` with the **correct** field values (the
   answer key). Leave a field as `""` when the document genuinely has no value
   (e.g. an open-ended labor contract has no `ngay_het_han`) — it won't be scored.
4. From the repo root, with keys exported:

   ```bash
   export GEMINI_API_KEY=...        # or GOOGLE_API_KEY
   export CLAUDE_API_KEY=...
   python -m backend.modules.extraction.benchmark.runner \
       --manifest backend/modules/extraction/benchmark/fixtures/manifest.json \
       --providers gemini_flash,claude_haiku,claude_sonnet \
       --out docs/benchmark_vision_extraction_v0.1.results.md
   ```

## Ground-truth field keys

`doi_tac`, `ngay_hieu_luc`, `ngay_het_han`, `gia_tri_hd`, `thoi_han_hd`,
`dieu_khoan_gia_han`, `dieu_khoan_thanh_toan`.

Scored target fields (issue #3): `ngay_het_han`, `gia_tri_hd`, `doi_tac`, `thoi_han_hd`.
Comparison is normalized (date layout, thousand separators, casing/accents ignored).
