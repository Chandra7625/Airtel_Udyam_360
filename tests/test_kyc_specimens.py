"""Regression: expected KYC outcome for each specimen applicant (from cached OCR extractions)."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from modules.kyc_checks import validate_applicant, summarise, gstin_checksum_ok, mask_gstin, mask_id

EXPECTED = {  # applicant: (status, codes that must be present)
    "K01": ("needs_correction", {"UDYAM_MISSING", "GSTIN_STATUS"}),   # blank Udyam no. + cancelled GSTIN
    "K02": ("pass", set()),                                            # skewed scan, read after deskew
    "K03": ("pass", set()), "K05": ("needs_review", {"UDYAM_ABSENT"}),
    "K04": ("needs_review", {"GST_PRESENT"}),                          # blurry GST scan
    "K06": ("needs_correction", {"GSTIN_FORMAT"}),                     # tampered digit
    "K07": ("needs_correction", {"GST_PROP_MISMATCH"}),                # proprietor name swapped
    "K08": ("pass", set()), "K09": ("pass", set()), "K10": ("pass", set()),
    "K11": ("needs_correction", {"ADDR_STALE"}),                       # bill 257 days old
    "K12": ("pass", set()),
}

def test_all_specimens():
    for kid, (status, codes) in EXPECTED.items():
        d = json.loads((ROOT / "data" / "kyc_extractions" / f"{kid}.json").read_text())["docs"]
        s = summarise(validate_applicant(d))
        got = {c["code"] for c in s["errors"] + s["warnings"]}
        assert s["status"] == status, (kid, s["status"], got)
        assert codes <= got, (kid, codes, got)

def test_checksum_and_masking():
    assert gstin_checksum_ok("37IHKXV5167L1ZS") and not gstin_checksum_ok("37IHKXV5167L1ZT")
    assert "IHKXV5167" not in mask_gstin("37IHKXV5167L1ZS") and mask_id("SYN-ID-346190") == "*********6190"
