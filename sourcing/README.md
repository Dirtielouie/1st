# Sourcing Aligned (design control / DHF)

Cible : responsables R&D et CTO chez des fabricants de dispositifs médicaux
(siège et personne en France, DACH, Benelux), source Lemlist People Database.

Recherches sauvegardées dans Lemlist :
- `Aligned – CTO MedTech FR/DACH/Benelux`
- `Aligned – Resp. R&D MedTech FR/DACH/Benelux`

`score_dhf.py` note chaque lead selon son exposition au DHF :
- entreprise : dispositifs médicaux, réglementée (ISO 13485, MDR/IVDR, FDA, CE),
  conçoit/fabrique en interne ;
- personne : design control, gestion des risques (ISO 14971), IEC 62304, V&V, réglementaire ;
- exclusions : distributeurs, consultants, prothésistes/labos dentaires, pharmacies…
  (seulement si l'entreprise ne montre aucune activité de conception ou fabrication) ;
- hors zone : personne basée hors France/DACH/Benelux.

Tiers : A ≥ 60, B ≥ 35, C < 35, X = exclu.

    python3 score_dhf.py prospects_dhf.csv raw/*.json

Les CSV générés contiennent des données personnelles et ne sont pas versionnés.
