#!/usr/bin/env python3
"""Génère un organigramme HTML à partir d'un export JSON de la base Lemlist
(résultat de lemleads_search en mode "people", filtré sur l'URL LinkedIn de
l'entreprise).

Usage :
    python3 orgchart.py data/easymedstat.json output/easymedstat.html "EasyMedStat"

La hiérarchie est déduite des intitulés de poste : les liens hiérarchiques
sont des hypothèses, pas des données LinkedIn.
"""
import html
import json
import sys

# Département -> mots-clés cherchés dans l'intitulé (minuscules).
DEPARTMENTS = [
    ("Direction", ["ceo", "founder", "fondateur", "fondatrice", "président", "directeur général", "managing director", "coo", "cfo"]),
    ("Commercial", ["sales", "account executive", "business", "commercial", "sdr", "bizdev", "customer success", "partnership"]),
    ("Tech & Produit", ["cto", "tech", "développeur", "developer", "dev ", "engineer", "ingénieur", "qa", "data", "product", "produit"]),
    ("Marketing", ["marketing", "growth", "communication", "content"]),
    ("Opérations & Clinique", ["clinique", "clinical", "projet", "project", "operations", "biostat", "statisticien", "regulatory"]),
    ("RH & Finance", ["rh", "hr", "people", "talent", "finance", "comptab", "juridique", "legal"]),
]
# Intitulés qui désignent un responsable d'équipe dans son département.
MANAGER_WORDS = ["head", "lead", "director", "directeur", "directrice", "vp", "chief", "responsable", "manager"]
SENIORITY_RANK = {
    "Ownership / Firm Leadership": 0, "Executive Leadership": 1, "Department Leadership": 2,
    "People Management / Leadership": 3, "Upper Mid-Level / Experienced IC": 4,
    "Mid-Level (Individual Contributor)": 5, "Entry-Level": 6,
}


def current_role(person, company):
    """Expérience en cours dans l'entreprise ciblée (sinon le headline)."""
    key = company.lower().replace(" ", "")
    for exp in person.get("experiences", []):
        name = (exp.get("company_name", "") + exp.get("company_linkedin_url", "")).lower().replace(" ", "")
        if key in name and not exp.get("date_to"):
            return exp.get("title") or "", exp.get("date_from") or ""
    return person.get("headline", ""), ""


def classify(title):
    t = title.lower() + " "
    for dept, words in DEPARTMENTS:
        if any(w in t for w in words):
            return dept
    return "Autres"


def build(people, company):
    rows = []
    for p in people:
        title, since = current_role(p, company)
        rows.append({
            "name": p.get("full_name", "?"),
            "title": title,
            "since": since,
            "location": (p.get("location") or "").split(",")[0],
            "url": p.get("lead_linkedin_url", ""),
            "dept": classify(title),
            "rank": SENIORITY_RANK.get(p.get("seniority"), 5),
            "is_manager": any(w in title.lower() for w in MANAGER_WORDS),
        })
    rows.sort(key=lambda r: (r["rank"], r["name"]))
    direction = [r for r in rows if r["dept"] == "Direction"]
    depts = {}
    for r in rows:
        if r["dept"] != "Direction":
            depts.setdefault(r["dept"], []).append(r)
    return direction, depts


def card(r, cls=""):
    initials = "".join(w[0] for w in r["name"].split()[:2]).upper()
    meta = " · ".join(x for x in [r["location"], f"depuis {r['since']}" if r["since"] else ""] if x)
    name = html.escape(r["name"])
    if r["url"]:
        name = f'<a href="{html.escape(r["url"])}" target="_blank" rel="noopener">{name}</a>'
    return (f'<div class="card {cls}"><div class="av">{html.escape(initials)}</div><div>'
            f'<div class="nm">{name}</div><div class="tt">{html.escape(r["title"])}</div>'
            f'<div class="mt">{html.escape(meta)}</div></div></div>')


def render(direction, depts, company, total):
    cols = []
    for dept, members in sorted(depts.items(), key=lambda kv: -len(kv[1])):
        leads = [m for m in members if m["is_manager"]][:1]
        others = [m for m in members if m not in leads]
        body = "".join(card(m, "lead") for m in leads)
        if others:
            body += '<div class="team">' + "".join(card(m) for m in others) + "</div>"
        cols.append(f'<section class="dept"><h2>{html.escape(dept)} <span>{len(members)}</span></h2>{body}</section>')
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Organigramme {html.escape(company)}</title>
<style>
:root{{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--mute:#6b7280;--line:#d6dae1;--acc:#0a66c2;--accbg:#e8f1fb}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14161b;--card:#1e2128;--ink:#e8eaee;--mute:#9aa1ad;--line:#343944;--acc:#70b5f9;--accbg:#1d2b3c}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.4 system-ui,-apple-system,Segoe UI,sans-serif;padding:24px 16px}}
header{{text-align:center;margin-bottom:24px}}h1{{margin:0 0 4px;font-size:24px}}header p{{margin:0;color:var(--mute)}}
.top{{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;position:relative;padding-bottom:24px}}
.top::after{{content:"";position:absolute;bottom:0;left:50%;height:24px;border-left:2px solid var(--line)}}
.depts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;border-top:2px solid var(--line);padding-top:20px}}
.dept h2{{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);margin:0 0 10px}}
.dept h2 span{{background:var(--accbg);color:var(--acc);border-radius:10px;padding:1px 8px;margin-left:4px}}
.team{{margin-left:14px;padding-left:12px;border-left:2px solid var(--line);display:flex;flex-direction:column;gap:8px;margin-top:8px}}
.card{{display:flex;gap:10px;align-items:flex-start;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;min-width:220px}}
.card.boss{{border-color:var(--acc);box-shadow:0 2px 8px rgba(10,102,194,.12)}}.card.lead{{border-left:4px solid var(--acc)}}
.av{{flex:none;width:36px;height:36px;border-radius:50%;background:var(--accbg);color:var(--acc);display:grid;place-items:center;font-weight:600;font-size:13px}}
.nm{{font-weight:600}}.nm a{{color:inherit;text-decoration:none}}.nm a:hover{{color:var(--acc);text-decoration:underline}}
.tt{{color:var(--ink)}}.mt{{color:var(--mute);font-size:12px}}
footer{{margin-top:28px;color:var(--mute);font-size:12px;text-align:center}}
</style></head><body>
<header><h1>{html.escape(company)}</h1><p>{total} collaborateurs identifiés · organigramme déduit des intitulés de poste</p></header>
<div class="top">{''.join(card(r, 'boss') for r in direction)}</div>
<div class="depts">{''.join(cols)}</div>
<footer>Source : base de contacts Lemlist (profils LinkedIn publics). Rattachements hiérarchiques supposés, à vérifier.</footer>
</body></html>"""


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    src, out, company = sys.argv[1:]
    data = json.load(open(src, encoding="utf-8"))
    people = data["results"] if isinstance(data, dict) else data
    direction, depts = build(people, company)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(direction, depts, company, len(people)))
    print(f"{len(people)} personnes -> {out}")


if __name__ == "__main__":
    main()
