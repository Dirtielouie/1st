# Routine hebdo : sourcing Aligned (mardi 9h, Europe/Zurich)

Chaque mardi, une session Claude fraîche exécute ces étapes et le résumé
final part par email (notification de la Routine).

1. `git fetch origin claude/sourcing-prospects-rnd-cto-c2gqcj && git checkout claude/sourcing-prospects-rnd-cto-c2gqcj && git pull`
2. Lemlist `lemleads_search`, mode `people`, `size: 100`, `seed: "aligned1"`, toutes les pages,
   avec les filtres des deux recherches sauvegardées (voir ci-dessous). Chaque réponse est
   enregistrée dans un fichier par l'outil : copier chaque fichier en `.json` dans
   `$SCRATCH/raw/`, préfixé `cto_` ou `rd_`.
3. `python3 -I sourcing/score_dhf.py $SCRATCH/prospects.csv $SCRATCH/raw/*.json`
4. Retenir les **50** meilleurs leads de tier A puis B dont le `lead_id` n'est pas dans
   `sourcing/sent_ids.txt` (une personne = un nom ; ignorer les doublons de nom).
5. `push_contacts_from_people_database` avec ces `lead_id`, `listId: clt_iJ26xRCGbJ2mfbtK3`
   (« Aligned – À valider »), **sans** `enrichFeatures` (pas de crédits).
6. Ajouter les `lead_id` poussés à `sourcing/sent_ids.txt`, commit, push sur la branche.
7. Message final en français (c'est lui qui part par email) : nombre de profils, répartition
   A/B et CTO/R&D, tableau des 10 meilleurs (nom, poste, entreprise, pays, pourquoi),
   rappel : valider dans Lemlist en déplaçant vers « Aligned – Validés »
   (`clt_9oMGnFyWoqyrdaB4P`) et supprimer les autres de « Aligned – À valider ».
   Si le stock A/B non envoyé passe sous 100, le signaler.

Ne jamais lancer de campagne, d'enrichissement payant ni d'envoi d'email à des prospects.

## Filtres

Communs : `currentCompanySubIndustry` in `Medical Equipment Manufacturing` ;
`currentCompanyCountry` in France, Germany, Switzerland, Austria, Belgium, Netherlands, Luxembourg.

- CTO : `currentTitle` in CTO, Chief Technology Officer, Directeur Technique ;
  out CIO, Chief Information Officer, Sales.
- R&D : `currentTitle` in Head of R&D, R&D Director, VP R&D, R&D Manager, Directeur R&D,
  Responsable R&D, Leiter Forschung und Entwicklung, Head of Research and Development ;
  out Intern, Stagiaire, Assistant ; `seniority` in People Management / Leadership,
  Department Leadership, Executive Leadership.
