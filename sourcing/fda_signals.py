"""Pull free regulatory signals from openFDA for medical device makers in FR/DACH/Benelux.

Signals (all public, no API key needed under 1,000 requests/day):
- 510(k) clearances: a recent clearance means an active DHF that was just audited by FDA.
- Registration & listing: establishments registered as "Specification Developer" own the
  device design, hence the DHF.
- Enforcement reports (recalls) whose reason mentions design: design control pain.

Usage: python3 fda_signals.py OUT_DIR [--since YYYYMMDD]
Requires network access to api.fda.gov.
"""
import argparse
import csv
import json
import os
import urllib.parse
import urllib.request

COUNTRIES = ["FR", "DE", "CH", "AT", "BE", "NL", "LU"]
API = "https://api.fda.gov/device"


def fetch_all(endpoint, search, sort=None, cap=5000):
    """Page through an openFDA endpoint (limit 1000 per call, skip <= 25000)."""
    rows, skip = [], 0
    while skip < cap:
        params = {"search": search, "limit": 1000, "skip": skip}
        if sort:
            params["sort"] = sort
        url = f"{API}/{endpoint}.json?" + urllib.parse.urlencode(params, safe=":[]+")
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 404:  # openFDA answers 404 when nothing matches
                break
            raise
        batch = data.get("results", [])
        rows.extend(batch)
        if len(batch) < 1000:
            break
        skip += 1000
    return rows


def country_clause(field):
    return "(" + "+OR+".join(f"{field}:{c}" for c in COUNTRIES) + ")"


def clearances(since):
    search = f"{country_clause('country_code')}+AND+decision_date:[{since}+TO+29991231]"
    for r in fetch_all("510k", search, sort="decision_date:desc"):
        yield {
            "signal": "510(k)", "date": r.get("decision_date"), "company": r.get("applicant"),
            "country": r.get("country_code"), "city": r.get("city"),
            "detail": f"{r.get('device_name')} ({r.get('k_number')}, {r.get('product_code')})",
            "device_class": (r.get("openfda") or {}).get("device_class"),
        }


def spec_developers():
    search = f"{country_clause('registration.iso_country_code')}+AND+establishment_type:\"Specification Developer\""
    seen = set()
    for r in fetch_all("registrationlisting", search):
        reg = r.get("registration") or {}
        name = reg.get("name")
        if name in seen:
            continue
        seen.add(name)
        classes = sorted({(p.get("openfda") or {}).get("device_class") or "" for p in r.get("products") or []} - {""})
        yield {
            "signal": "Specification Developer", "date": "", "company": name,
            "country": reg.get("iso_country_code"), "city": reg.get("city"),
            "detail": ", ".join(r.get("establishment_type") or []),
            "device_class": "/".join(classes),
        }


def design_recalls(since):
    search = (f"{country_clause('country')}+AND+report_date:[{since}+TO+29991231]"
              "+AND+(reason_for_recall:design+OR+reason_for_recall:conception)")
    for r in fetch_all("enforcement", search, sort="report_date:desc"):
        yield {
            "signal": f"Recall {r.get('classification', '')}".strip(), "date": r.get("report_date"),
            "company": r.get("recalling_firm"), "country": r.get("country"), "city": r.get("city"),
            "detail": (r.get("reason_for_recall") or "")[:300], "device_class": "",
        }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir")
    ap.add_argument("--since", default="20250101")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    for name, rows in [
        ("fda_510k.csv", clearances(args.since)),
        ("fda_spec_developers.csv", spec_developers()),
        ("fda_design_recalls.csv", design_recalls(args.since)),
    ]:
        rows = list(rows)
        path = os.path.join(args.out_dir, name)
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["signal", "date", "company", "country", "city", "detail", "device_class"])
            w.writeheader()
            w.writerows(rows)
        print(f"{path}: {len(rows)} lignes")


if __name__ == "__main__":
    main()
