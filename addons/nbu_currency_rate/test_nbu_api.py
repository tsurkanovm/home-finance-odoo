#!/usr/bin/env python3
"""
Standalone demo: Fetch currency rates from NBU (National Bank of Ukraine)
=========================================================================

Run this script outside of Odoo to verify the API works and see the output.
No API key required — the NBU endpoint is completely public and free.

Usage:
    python3 test_nbu_api.py                   # latest rates
    python3 test_nbu_api.py 2026-03-20        # rates for a specific date

Output shows:
    1. Raw API response (first 3 currencies)
    2. USD, EUR, UAH rates as Odoo would store them (company currency = UAH)
    3. USD, UAH rates if your company currency were EUR (cross-conversion)
"""

import json
import sys
from datetime import datetime

import requests

NBU_API_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"

# Currencies you care about
INTERESTING = {"USD", "EUR", "GBP", "PLN", "CHF", "JPY", "CAD"}


def fetch_nbu_rates(date_str=None):
    """Fetch rates from NBU. Returns list of dicts."""
    params = {"json": ""}
    if date_str:
        params["date"] = date_str.replace("-", "")

    resp = requests.get(NBU_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 70)
    print("  NBU Currency Rate API — Demo")
    print("=" * 70)
    print()

    if date_str:
        print(f"Fetching rates for date: {date_str}")
    else:
        print("Fetching latest available rates...")

    records = fetch_nbu_rates(date_str)

    # --- 1. Raw response (sample) -------------------------------------------
    print(f"\n1) Raw API response ({len(records)} currencies total)")
    print("   First 3 records:\n")
    for rec in records[:3]:
        print(f"   {json.dumps(rec, ensure_ascii=False, indent=6)}")

    # --- 2. Build lookup dict ------------------------------------------------
    uah_rates = {}
    for rec in records:
        code = rec.get("cc", "").upper()
        rate = rec.get("rate")
        if code and rate:
            uah_rates[code] = float(rate)

    # --- 3. Rates for company_currency = UAH ---------------------------------
    print("\n2) Odoo rates when company currency = UAH")
    print("   (Odoo stores: UAH_per_foreign_unit directly)\n")
    print(f"   {'Currency':<8} {'NBU rate (UAH/unit)':<22} {'Odoo rate':>14}")
    print(f"   {'--------':<8} {'---------------------':<22} {'-----------':>14}")

    for code in sorted(INTERESTING):
        nbu = uah_rates.get(code)
        if nbu:
            odoo_rate = nbu  # stored as-is: UAH per 1 foreign unit
            print(f"   {code:<8} {nbu:<22.4f} {odoo_rate:>14.8f}")

    # --- 4. Cross-conversion example: company = EUR --------------------------
    print("\n3) Cross-conversion example: company currency = EUR")
    print("   Formula: odoo_rate = UAH_per_foreign / UAH_per_EUR\n")

    eur_uah = uah_rates.get("EUR")
    if eur_uah:
        for code in ["USD", "GBP", "PLN", "UAH"]:
            if code == "EUR":
                continue
            if code == "UAH":
                # EUR per 1 UAH = 1 / (UAH per EUR)
                odoo_rate = 1.0 / eur_uah
                print(f"   EUR → UAH: 1 EUR = {eur_uah:.4f} UAH"
                      f"   →  Odoo rate for UAH = {odoo_rate:.8f}")
            else:
                foreign_uah = uah_rates.get(code)
                if foreign_uah:
                    odoo_rate = foreign_uah / eur_uah
                    print(f"   EUR → {code}: {foreign_uah:.4f} / {eur_uah:.4f}"
                          f"   →  Odoo rate = {odoo_rate:.8f}")

    # --- 5. Single-currency fetch example ------------------------------------
    print("\n4) Single-currency fetch (USD only):\n")
    single = requests.get(
        NBU_API_URL,
        params={"valcode": "USD", "json": ""},
        timeout=30,
    ).json()
    for rec in single:
        print(f"   {json.dumps(rec, ensure_ascii=False)}")

    print("\n" + "=" * 70)
    print("  Done! All data sourced from https://bank.gov.ua")
    print("=" * 70)


if __name__ == "__main__":
    main()
