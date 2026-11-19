# Corrigé — TP Inside the Feed

Toutes les valeurs ont été **calculées sur le corpus final** avec `python scripts/verifier_resultats.py`
et sont garanties par `tests/test_scenarios.py` et `tests/test_recommender.py`.
Scores arrondis à 3 ou 4 décimales. Corpus : 40 posts, 564 termes.

---

## Expérience A — Trois textes → vecteurs

**A.1** T1 → `match, football, stade` ; T2 → `voyage, stade, barcelone` ; T3 → `recette, tajine, marocain`.
Les mots `le, de, au, du` sont des **mots vides** : ils apparaissent partout et n'aident pas à distinguer les textes.

**A.2** `stade` est présent dans 2 textes sur 3 : idf = ln(4/3) + 1 = **1,2877**.
`match` n'est présent que dans T1 : idf = ln(4/2) + 1 = **1,6931**. Un mot partagé est moins discriminant.

**A.3** Vecteur brut de T1 = (1,6931 ; 1,6931 ; 1,2877), norme = √(2 × 1,6931² + 1,2877²) = **2,7187**.
Poids de `match` = 1,6931 / 2,7187 = **0,6228** (et `stade` = 1,2877 / 2,7187 = 0,4736).

**A.4** cos(T1, T2) = **0,2243** = 0,4736 × 0,4736 : seul `stade` est commun.

**A.5** cos(T1, T3) = **0** : aucun mot commun. Le résultat est juste du point de vue du vocabulaire,
mais le modèle ne « sait » pas que football et cuisine sont des sujets différents. Il ne voit que des mots.

**A.6** Avec T3 = « Tajine à Barcelone après le match » → `tajine, barcelone, match`.
`match` et `barcelone` passent dans 2 textes : leur idf tombe à **1,2877**.
Les trois cosinus deviennent égaux : cos(T1,T2) = cos(T1,T3) = cos(T2,T3) = **0,2682**.
Deux leçons : l'idf dépend **du corpus entier**, et un seul texte ajouté modifie toutes les similarités.

## Expérience B — Cosinus entre deux posts

| Paire | Cosinus | Termes communs (contribution) |
|---|---|---|
| p01 / p04 (deux posts football) | **0,177** | supporters 0,0713 · stade 0,0403 · match 0,0357 · équipe 0,0178 · football 0,0121 |
| p07 / p25 (foot entre amis / e-sport) | **0,271** | tournoi 0,2029 · dimanche 0,0676 |
| p01 / p07 (football / foot) | **0,000** | aucun |

**B.2** Oui, c'est surprenant : deux thèmes différents (football amateur et jeu vidéo) sont plus
« similaires » que deux posts football. `tournoi` est rare dans le corpus (idf élevé) et pèse lourd
dans ces deux textes courts. **Le cosinus mesure le vocabulaire partagé, pas le thème.**

**B.3** p07 écrit `foot`, p01 écrit `football` : pour le modèle, ce sont deux termes sans rapport.
Problème de **synonymes / variantes lexicales**.

**B.4** Pistes : un dictionnaire de normalisation (`foot` → `football`) ; une racinisation ou une lemmatisation ;
des n-grammes de caractères (`analyzer="char_wb"`) qui rapprochent `foot` et `football` ;
des plongements sémantiques (word embeddings, sentence embeddings) qui rapprochent les synonymes.

## Expérience C — Football, puis voyage

**C.1** Likes p01, p02, p03 :

| Rang | Post | Thème | Score |
|---|---|---|---|
| 1 | p04 Coupe d'Afrique | football | 0,148 |
| 2 | p06 Ballon d'or | football | 0,116 |
| 3 | p08 Mode carrière (jeu vidéo de foot) | gaming | 0,109 |
| 4 | p35 VAR et capteurs | technologie | 0,088 |
| 5 | p09 Week-end à Barcelone | voyage | 0,085 |
| 6 | p25 Tournoi e-sport | gaming | 0,067 |
| 7 | p05 Entraînement du gardien | football | 0,050 |
| 8 | p18 Pâtes crémeuses | cuisine | 0,029 |

Les thèmes affichés ne sont pas tous « football » : les posts **mixtes** (p08, p35, p09) partagent du vocabulaire football.

**C.2** p04 : supporters 0,217 × 0,271 = 0,0589 ; match 0,0294 ; stade 0,0218 ; football 0,0197 ; équipe 0,0187.
Somme = **0,1484** = score affiché.

**C.3** p18 (Pâtes crémeuses), à cause du **seul** terme `rapide` (0,085 × 0,343 = 0,0292) :
« Rapide et précis devant le but » (p03) contre « une recette rapide » (p18).
C'est la **polysémie** : même mot, sens différent. Le modèle ne comprend pas le contexte.
*(Remarque : `rapides` au pluriel, dans p02, est un autre terme ; seul `rapide`, issu de p03, est partagé.)*

**C.4** Après l'ajout de p10 :

| Post | Rang avant → après | Évolution |
|---|---|---|
| p09 Barcelone | 5 → 2 | ▲ 3 |
| p15 Jemaa el-Fna | 12 → 6 | 🆕 entre |
| p14 Billets d'avion | 16 → 8 | 🆕 entre |
| p05 Gardien | 7 → 10 | ❌ sort |
| p18 Pâtes | 8 → 12 | ❌ sort |

p04 reste premier (0,148 → 0,131). Tous les scores football baissent légèrement : le profil est
renormalisé, donc les poids football sont « dilués » par les nouveaux termes.

**C.5** p09 contient **les deux** vocabulaires : football 0,0323 + voyage 0,0272 + match 0,0242 + stade 0,0179 + jours 0,0140.
Il gagne des points sur le terme `voyage` sans perdre ses termes football.
*(`jours` vient de « dix jours de route » dans p10 et de « trois jours » dans p09 : encore une coïncidence de vocabulaire.)*
De même, p15 gagne grâce à `marrakech` (0,0301), présent dans p10, et à `voyage`.

**C.6** Après l'ajout, `désert` passe en tête du profil (0,199). p10 contient `désert` deux fois (texte + hashtag),
et c'est un terme très rare (idf 4,02). Un seul like peut donc peser lourd si son vocabulaire est rare et
concentré. La moyenne ne pondère pas les likes selon leur ancienneté ou leur intensité.

## Expérience D — Exploration

**D.1** Top 8 à 0 % : football, voyage, gaming, technologie. **Absents : cuisine, fitness.**

**D.2** arrondi(8 × 0,25) = **2 places**. Choix : **p18** (cuisine, 0,026) en position 4 et **p36** (fitness, 0,013) en position 8.
Ils remplacent les deux derniers posts de pertinence (p25 et p14).

**D.3** Non. Les scores affichés sont identiques à ceux du classement pur (p18 = 0,0257 à 0 % comme à 25 %,
rang 12). Le test `test_exploration_themes_absents_et_scores_inchanges` le vérifie.

**D.4** À 50 % : 4 places → p18 (cuisine), p36 (fitness), p21 (cuisine), p38 (fitness), insérés en positions 2, 4, 6 et 8.
Règle : on alterne les thèmes absents dans l'ordre fixe (cuisine puis fitness) et on prend chaque fois
le meilleur post non aimé restant du thème.

**D.5** Avec football seul, le top 8 couvre déjà 5 thèmes (football, voyage, cuisine via p18, gaming, technologie) :
**seul fitness est absent**, donc les deux places vont à p36 et p38.

**D.6** Non. Le modèle NLP calcule les scores (`model.py`) ; l'exploration est une **règle d'affichage**
(`feed.py`) qui choisit quels posts montrer, sans modifier les scores. On peut changer l'une sans toucher à l'autre.

## Synthèse

1. **Contenu** : on recommande ce qui ressemble aux contenus aimés (ici, ressemblance des textes).
   **Collaboratif** : on recommande ce qu'ont aimé des utilisateurs aux goûts proches (il faut beaucoup d'utilisateurs).
   **Hybride** : combinaison des deux, avec souvent d'autres signaux. **Ici : basé sur le contenu uniquement.**
2. **Cold start** : sans historique, pas de profil. L'application affiche un feed initial équilibré, déterministe
   et explicitement non personnalisé.
3. Exemples : synonymes (`foot`/`football`, cos(p01,p07) = 0) ; polysémie (`rapide` → p18) ; pas de lemmatisation
   (`joueur`/`joueurs`, `maroc`/`marocain`) ; coïncidences (`soir` relie p15 à p01) ; surspécialisation
   (le feed suit les likes passés) ; vocabulaire figé au corpus (un mot nouveau est ignoré).
4. Le cosinus mesure un angle entre vecteurs de mots. Il n'est ni calibré, ni appris sur des comportements réels.
   Une valeur de 0,15 ne signifie pas « 15 % de chances d'aimer ».
5. Non : un utilisateur fictif, 40 posts, quelques clics. Il faudrait de vrais utilisateurs sur une durée longue,
   une mesure de diversité (entropie des thèmes vus), un groupe témoin (avec et sans personnalisation)
   et un protocole statistique.
6. Dans `rank_by_similarity` :
   `ranking = [(pid, float(scores[i])) for i, pid in enumerate(model.ids) if pid not in liked]`.
   L'exploration réutilise ce classement, donc elle exclut aussi les posts aimés.
