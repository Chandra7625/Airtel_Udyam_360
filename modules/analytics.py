from pathlib import Path
import pandas as pd
import numpy as np

DATA = Path(__file__).resolve().parents[1] / "data"
STAGES = [
    ("Lead", 5000), ("Contacted", 3406), ("Needs assessed", 1974),
    ("Quote accepted", 861), ("KYC complete", 588), ("Activated", 368)
]
REASONS = [
    "Competitor offered cheaper plan", "Quote took too long to arrive",
    "Not interested on first call", "Installation delayed beyond 21 days",
    "Quote too complex to understand", "Document details did not match",
    "Owner had no time for a visit", "Locked in with current provider",
    "Price too high", "Decided to wait"
]

def generate_synthetic_leads():
    p = DATA / "synthetic_leads.csv"
    rng = np.random.default_rng(42)
    n = 5000
    labels = np.array(
        ["Lead"] * 1594 + ["Contacted"] * 1432 + ["Needs assessed"] * 1113 +
        ["Quote accepted"] * 273 + ["KYC complete"] * 220 + ["Activated"] * 368
    )
    rng.shuffle(labels)
    seg = rng.choice(
        ["Micro retail & services", "Professional offices",
         "Small multi-site businesses", "Small manufacturers"],
        n, p=[.55, .25, .15, .05]
    )
    df = pd.DataFrame({
        "lead_id": [f"SYN{i+1:05d}" for i in range(n)],
        "created_date": pd.date_range("2026-04-01", periods=n, freq="30min").strftime("%Y-%m-%d"),
        "lead_source": rng.choice(["Field sales", "Website form", "Channel partner", "Inbound call", "Referral", "WhatsApp campaign"], n),
        "business_name": [f"Demo Business {i+1}" for i in range(n)],
        "business_type": rng.choice(["Kirana store", "Clinic", "Coaching centre", "Restaurant", "Auto-parts unit", "Salon"], n),
        "segment": seg, "city": rng.choice(["Chennai", "Bengaluru", "Mumbai", "Kolkata", "Pune", "Hyderabad"], n),
        "city_tier": rng.choice([1, 2], n), "state": rng.choice(["Tamil Nadu", "Karnataka", "Maharashtra", "West Bengal", "Telangana"], n),
        "preferred_language": rng.choice(["English", "Hindi", "Tamil", "Bengali"], n),
        "employee_count": rng.integers(1, 100, n), "num_sites": rng.integers(1, 8, n),
        "annual_turnover_band": rng.choice(["< 40 lakh", "40 lakh - 1.5 cr", "1.5 - 5 cr", "5 - 25 cr"], n),
        "has_gstin": rng.choice(["Y", "N"], n, p=[.7, .3]), "gstin": "",
        "has_udyam": rng.choice(["Y", "N"], n), "udyam_number": "",
        "current_internet": rng.choice(["Mobile hotspot", "Home broadband", "Business broadband", "Leased line", "None"], n),
        "current_provider": rng.choice(["Competitor A", "Competitor B", "Accel", "Local ISP"], n),
        "monthly_telecom_spend_inr": rng.integers(300, 15000, n), "products_of_interest": "",
        "contact_name": "Demo Contact", "contact_role": "Owner", "stage_reached": labels,
        "outcome": np.where(labels == "Activated", "Activated", "Dropped"),
        "drop_reason": ["" if s == "Activated" else rng.choice(REASONS) for s in labels],
        "contacted_date": "", "needs_assessed_date": "", "quote_accepted_date": "",
        "kyc_complete_date": "", "activated_date": "",
        "days_lead_to_activation": np.where(labels == "Activated", rng.integers(5, 30, n), np.nan),
        "customer_follow_up_calls": rng.integers(0, 5, n), "bundle_products": "",
        "monthly_bundle_value_inr": np.where(labels == "Activated", rng.integers(1500, 30000, n), np.nan),
        "one_time_setup_inr": np.where(labels == "Activated", rng.integers(0, 10000, n), np.nan),
        "contract_months": np.where(labels == "Activated", 12, np.nan),
        "churned_within_6_months": np.where(labels == "Activated", rng.choice(["Y", "N"], n, p=[.12, .88]), ""),
        "nps_score": np.where(labels == "Activated", rng.integers(4, 11, n), np.nan),
        "acquisition_cost_inr": rng.integers(120, 4500, n)
    })
    df.to_csv(p, index=False)
    return df

def load_leads():
    """Use the original case dataset when present; otherwise generate clearly labelled demo data."""
    original = DATA / "smb_leads.csv"
    if original.exists():
        return pd.read_csv(original), "data/smb_leads.csv"
    synthetic = DATA / "synthetic_leads.csv"
    if synthetic.exists():
        return pd.read_csv(synthetic), "data/synthetic_leads.csv (synthetic demo data)"
    return generate_synthetic_leads(), "data/synthetic_leads.csv (synthetic demo data)"
