# Udyam360 — Hackathon MVP

## Data folder setup
Place these files in `data/`:
- `product_catalogue.csv`
- `mock_gstin_registry.csv`
- `mock_udyam_registry.csv`
- `smb_leads.csv` (your original lead dataset)
- `kyc_documents/` (folder containing all supplied K01–K12 specimen files)

The app automatically uses `smb_leads.csv` if present. It falls back to generated synthetic leads only if the original is absent. KYC specimen files are listed and previewed from `data/kyc_documents/`.

## Windows / VS Code
```powershell
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Copy `.env.example` to `.env` and add `GROQ_API_KEY`. The LLM is optional; the rule-based advisor fallback remains available.

## Demo flow
Home → AI Business Advisor → Bundle & Checkout → Smart KYC → Order Tracker → Sales Intelligence.

## Prototype boundaries
- GSTIN/Udyam checks use fictional mock registries, not live government APIs.
- OCR is integrated (see below). Registry checks use fictional mock data.
- Prices use catalogue midpoint estimates.
- Never commit `.env`, uploaded customer documents, or real personal data.

## Smart KYC: OCR + validation
`pip install -r requirements.txt` (RapidOCR is pip-only; no Tesseract/system install needed).

Pipeline per document: deskew -> sharpness check -> watermark removal -> RapidOCR -> label/geometry parser ->
GSTIN look-alike normalisation (O/0, I/1 by position). If the scan is blurry and a Groq key is set, a vision model
re-reads it; otherwise the fields are shown flagged so the user can correct them by hand.
Validators (`modules/kyc_checks.py`): GSTIN format + checksum (accepts X), registry status, legal/trade/proprietor name,
address match, cross-document name consistency, 90-day address proof (today = 2026-07-15), ID expiry, masking.

    python scripts/run_specimens.py --fresh   # re-OCR all 47 specimens -> data/kyc_extractions/*.json
    python -m pytest -q tests                 # locks in the expected outcome for K01-K12

Specimen outcomes: pass K02 K03 K08 K09 K10 K12 | review K04 (blurry) K05 (no Udyam) |
fail K01 (blank Udyam no. + cancelled GSTIN) K06 (tampered GSTIN) K07 (proprietor name swapped) K11 (stale bill).
