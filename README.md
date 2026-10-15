# 1st
It's to learn cde

## Organigramme de prospection

`orgchart.py` transforme un export de la base de contacts Lemlist (recherche
« people » filtrée sur l'URL LinkedIn de l'entreprise) en organigramme HTML.

```
python3 orgchart.py data/<entreprise>.json output/<entreprise>.html "<Entreprise>" [data/<entreprise>.corrections.json]
```

Les rattachements hiérarchiques sont déduits des intitulés de poste.
`data/` et `output/` ne sont pas versionnés (données personnelles).

Le fichier de corrections (optionnel) sert à retirer les départs et à ajouter
les personnes absentes de la base :
`{"remove": ["Nom"], "add": [{"full_name": "...", "title": "...", "seniority": "..."}]}`.
