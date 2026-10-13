"""Score Lemlist People Database leads on their exposure to design control / DHF.

Aligned (aligned.ch) sells a design control tool. A prospect is relevant when the
company designs medical devices in-house, and therefore has to maintain a Design
History File (FDA 21 CFR 820.30 / QMSR, ISO 13485 §7.3, MDR/IVDR technical file).

Usage: python3 score_dhf.py OUT.csv RAW.json [RAW.json ...]
RAW files are lemleads_search people-mode responses (detail compact).
"""
import csv
import json
import re
import sys

ZONE = {"France", "Germany", "Switzerland", "Austria", "Belgium", "Netherlands", "Luxembourg"}

TARGET_TITLE = re.compile(
    r"\b(cto|chief technology|chief technical|directeur technique|directrice technique|technical director"
    r"|r\s?&\s?d|research (and|&) development|recherche (et|&) d[ée]veloppement|forschung|entwicklung"
    r"|head of development|vp engineering|director of engineering|directeur de l'innovation|innovation)\b",
    re.I,
)

# Company signals, read from the current employer's description.
CO_MEDDEV = re.compile(
    r"medical device|medical technolog|medtech|dispositifs? m[ée]dica|medizinprodukt|medizintechn"
    r"|implant|in[- ]vitro|\bivd\b|diagnostic|surgical|chirurgi|catheter|cath[ée]ter|stent|orthop[ae]dic"
    r"|imaging|imagerie|monitoring|ventilat|infusion|dialys|hearing|audio|ophthalm|dental|dentaire",
    re.I,
)
CO_REG = re.compile(
    r"iso\s?13485|\bmdr\b|\bivdr\b|\bfda\b|510\s?\(?k\)?|\bpma\b|ce[- ]mark|marquage ce|ce[- ]kennzeichnung"
    r"|class(e)?\s?(ii|iii|2|3|iib|iia)\b|klasse\s?(ii|iii)|notified body|organisme notifi|benannte stelle",
    re.I,
)
CO_DESIGN = re.compile(
    r"\bdesign|develop|conception|con[çc]oi|d[ée]velopp|entwickel|entwicklung|\br\s?&\s?d\b|innovat|patent|brevet",
    re.I,
)
CO_MAKER = re.compile(r"manufactur|fabricant|fabriqu|herstell|produ[ck]", re.I)
# Always disqualifying: no in-house device design, so no DHF.
CO_NEG = re.compile(
    r"orthoproth|podo-orth|sanit[äa]tshaus|laboratoire dentaire|dentallabor|proth[ée]siste|pharmacie|apotheke"
    r"|opticien|optiker|hearing aid (shop|store)|audioproth",
    re.I,
)
# Disqualifying only when the company shows no design or manufacturing activity
# (manufacturers routinely say "distributed in 60 countries" or "consulting services").
CO_NEG_WEAK = re.compile(
    r"distribut|revendeur|wiederverk|vertriebspartner|h[äa]ndler|\bconsult|cabinet de conseil|beratung"
    r"|staffing|recrutement|recruit",
    re.I,
)

# Person signals, read from headline, summary, skills and job titles.
P_DESIGN_CONTROL = re.compile(
    r"design control|\bdhf\b|design history|design dossier|technical file|technische dokumentation"
    r"|dossier technique|documentation technique|iec\s?62304|iso\s?14971|risk management|gestion des risques"
    r"|risikomanagement|\bv\s?&\s?v\b|verification|v[ée]rification|validation|requirements|exigences"
    r"|traceab|tra[çc]abilit|usability|iec\s?62366|iec\s?60601",
    re.I,
)
P_REG = re.compile(r"iso\s?13485|\bmdr\b|\bivdr\b|\bfda\b|510\s?\(?k\)?|ce[- ]mark|marquage ce|regulatory|r[ée]glementaire", re.I)
P_DEV = re.compile(r"product development|d[ée]veloppement (de )?produit|produktentwicklung|\bnpi\b|new product", re.I)


def current_exp(lead):
    exps = lead.get("experiences") or []
    current = [e for e in exps if not e.get("date_to")]
    for e in current:
        if TARGET_TITLE.search(e.get("title") or ""):
            return e
    return current[0] if current else (exps[0] if exps else {})


def score(lead):
    exp = current_exp(lead)
    co_desc = exp.get("company_description") or ""
    person_txt = " ".join(
        [lead.get("headline") or "", lead.get("summary") or "", " ".join(map(str, lead.get("skills") or []))]
        + [e.get("title") or "" for e in lead.get("experiences") or []]
    )
    pts, why = 0, []
    if CO_MEDDEV.search(co_desc):
        pts += 25; why.append("entreprise dispositifs médicaux")
    if CO_REG.search(co_desc):
        pts += 20; why.append("réglementé (13485/MDR/FDA/CE)")
    if CO_DESIGN.search(co_desc):
        pts += 10; why.append("conçoit/développe en interne")
    if CO_MAKER.search(co_desc):
        pts += 5; why.append("fabricant")
    if P_DESIGN_CONTROL.search(person_txt):
        pts += 20; why.append("profil design control / risques / V&V")
    if P_REG.search(person_txt):
        pts += 10; why.append("profil réglementaire")
    if P_DEV.search(person_txt):
        pts += 5; why.append("développement produit")
    if not co_desc:
        why.append("pas de description entreprise")
    # Exclusion words often name the company's customers ("for pharmacies", "for audiologists"),
    # so they only disqualify when the description shows no design or manufacturing activity.
    builds = CO_DESIGN.search(co_desc) or CO_MAKER.search(co_desc)
    neg = None if builds else (CO_NEG.search(co_desc) or CO_NEG_WEAK.search(co_desc))
    if neg:
        pts -= 40; why.append(f"exclusion probable ({neg.group(0)})")
    elif CO_NEG.search(co_desc):
        pts -= 15; why.append(f"à vérifier ({CO_NEG.search(co_desc).group(0)})")
    size = exp.get("company_size") or ""
    if size == "1-10":
        pts -= 10; why.append("très petite structure")
    tier = "A" if pts >= 60 else "B" if pts >= 35 else "C"
    if neg:
        tier = "X"
    return pts, tier, exp, why


def main(out, paths):
    seen, rows = set(), []
    for p in paths:
        segment = "CTO" if "cto" in p.lower() else "R&D"
        for lead in json.load(open(p))["results"]:
            if lead["lead_id"] in seen:
                continue
            seen.add(lead["lead_id"])
            pts, tier, exp, why = score(lead)
            if lead.get("country") not in ZONE:
                tier, why = "X", why + ["basé hors zone"]
            rows.append({
                "tier": tier, "score": pts, "segment": segment,
                "name": lead.get("full_name"), "title": exp.get("title"),
                "company": exp.get("company_name"), "company_size": exp.get("company_size"),
                "company_country": exp.get("company_headquarters_country"), "lead_country": lead.get("country"),
                "linkedin": lead.get("lead_linkedin_url"), "company_website": exp.get("company_website_url"),
                "why": "; ".join(why), "lead_id": lead["lead_id"],
            })
    rows.sort(key=lambda r: ("ABCX".index(r["tier"]), -r["score"]))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
