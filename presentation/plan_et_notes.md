# Plan de la présentation et notes orales — 25 minutes

**Analyse avancée et IA : Recommandation et NLP appliqués au Web**
Binôme 10 — MASSOUANE Abdelati (**A**) & MOUATE Alaa Eddine (**M**)

Progression inspirée de la démarche des références : **comprendre → théorie pas à pas → démonstration →
code → observations → limites et conclusion**. Chaque partie se termine par un encadré « À retenir ».

| Partie | Slides | Durée | Qui |
|---|---|---|---|
| I. Contexte | 1–3 | 3 min | A |
| II. Du texte au vecteur (NLP) | 4–6 | 5 min | A |
| III. Du vecteur au feed | 7–8 | 3 min | M |
| IV. Démonstration | 9 | 6 min | M + A |
| V. Le code | 10 | 3 min | M |
| VI. Limites, comparaison, conclusion | 11–14 | 4 min | A + M |
| Questions | — | 1 min (+ selon le temps) | |

---

### Slide 1 — Titre (0:00–0:30) · A
**Contenu** : Inside the Feed · sujet · binôme · encadrant · année.
**À dire** : « Chaque jour, un feed choisit pour nous quelques publications parmi des milliers.
Aujourd'hui, nous ouvrons le capot d'un moteur simple, construit nous-mêmes, pour voir comment des textes
et des likes deviennent un classement. »

### Slide 2 — Plan (0:30–1:00) · A
Cinq parties numérotées 01 à 05, comme ci-dessus.

### Slide 3 — Contexte et problématique (1:00–3:00) · A
**Contenu** : trop de contenus pour tout voir ; le feed doit trier. Encadré **Problématique** :
*« Comment un système peut-il transformer des textes et des interactions en un feed personnalisé et explicable ? »*
Trois familles : **contenu**, **collaboratif**, **hybride** (une ligne chacune).
**À dire** : « Nous nous concentrons sur la première famille, la recommandation basée sur le contenu,
parce qu'elle s'explique entièrement et ne nécessite qu'un utilisateur. »
**À retenir** : le feed est un problème de **classement**.

### Slide 4 — Prétraitement : du texte aux tokens (3:00–4:30) · A
**Contenu** : exemple réel du post p01 (capture de l'onglet 🔬, étape ②) : tokens bleus, mots vides barrés.
50 tokens bruts → 29 conservés.
**À dire** : « Minuscules, découpage en mots, suppression des mots vides. Pas de lemmatisation :
“joueur” et “joueurs” restent deux mots différents. Nous en reparlerons dans les limites. »

### Slide 5 — TF-IDF (4:30–6:30) · A
**Contenu** : formule `tf × idf`, `idf = ln((1+n)/(1+df)) + 1`, normalisation L2.
Mini-tableau de l'expérience A : T1 = (football 0,623 ; match 0,623 ; stade 0,474).
**À dire** : « Un mot pèse lourd s'il est fréquent dans le post et rare dans le corpus.
“stade” apparaît dans deux textes sur trois : il pèse moins que “match”. »
**À retenir** : un post = un vecteur de 564 nombres, presque tous nuls (3,3 % non nuls).

### Slide 6 — Similarité cosinus (6:30–8:00) · A
**Contenu** : schéma de deux flèches et d'un angle ; `cos = Σ u[t] × v[t]` pour des vecteurs de longueur 1.
Exemple : cos(T1, T2) = 0,474 × 0,474 = 0,224 ; cos(T1, T3) = 0.
**À dire** : « Comme les vecteurs ont une longueur 1, le cosinus est une simple somme de produits.
C'est ce qui rend chaque recommandation explicable terme par terme. »

### Slide 7 — Le profil utilisateur (8:00–9:30) · M
**Contenu** : profil = moyenne des vecteurs aimés, renormalisée. Barres des termes du profil
(capture onglet 🔬, étape ④, scénario football : but, match, supporters…).
**À dire** : « L'utilisateur devient lui-même un vecteur, dans le même espace que les posts.
On peut donc le comparer à chaque post avec le cosinus. »

### Slide 8 — Du score au feed (9:30–11:00) · M
**Contenu** : pipeline en 6 cases (texte → tokens → TF-IDF → profil → scores → classement).
Trois règles : exclure les posts aimés ; trier par score ; **sans like → feed initial équilibré, non personnalisé**.
Encadré : « **score de similarité**, pas probabilité d'aimer ».

### Slide 9 — DÉMONSTRATION (11:00–17:00) · M aux commandes, A commente
Suivre `docs/demo.md` en **mode présentation** :
1. Cold start. 2. Trois likes football → p04 en tête, p18 grâce à « rapide ».
3. Ouvrir l'algorithme : la somme des contributions = le score.
4. Ajout de p10 → p09 ▲3, p15 et p14 entrent.
5. Exploration 25 % → p18 et p36, scores inchangés.
**Slide de secours** : captures d'écran des étapes 2 et 4 si la démo échoue.

### Slide 10 — Le code (17:00–20:00) · M
**Contenu** : architecture en deux blocs : `recommender/` (calculs, sans Streamlit) | `app.py` (affichage).
Quatre extraits courts : `preprocess` · `build_profile` · `term_contributions` · `build_feed`.
**À dire** : « Le cœur du moteur tient en une trentaine de lignes. Les explications affichées sont calculées
par le même code que les scores. 44 tests vérifient les calculs et les effets que nous venons de montrer. »

### Slide 11 — Exploration (20:00–21:00) · M
**Contenu** : règle (k = arrondi(8 × p) ; thèmes absents du top 8 ; meilleur post par thème, à tour de rôle).
**À dire** : « L'exploration n'est pas du NLP : c'est une règle de produit, séparée et réglable,
contre la surspécialisation. »

### Slide 12 — Limites observées (21:00–22:30) · A
**Contenu** : quatre exemples **tirés de la démo** :
synonymes (cos(p01, p07) = 0) · polysémie (« rapide ») · « foot » ≠ « tournoi e-sport » mais cos = 0,27 · cold start.
Puis : vocabulaire figé, pas de lemmatisation, surspécialisation.

### Slide 13 — Ce que la démo prouve / ne prouve pas (22:30–23:30) · A
✅ Un mécanisme complet et explicable.
❌ Pas l'algorithme de TikTok ou d'Instagram. ❌ Pas une preuve de bulle de filtre (un utilisateur fictif, 40 posts).
**Perspectives** : embeddings sémantiques, filtrage collaboratif, système hybride, mesure de diversité.

### Slide 14 — Conclusion (23:30–24:00) · M
Trois lignes : **TF-IDF** transforme le texte en vecteurs · **cosinus** compare · **le feed** classe et explore.
« Un feed n'est pas magique : c'est un calcul, et ce calcul a des limites. »

### Slide 15 — Merci / Questions (24:00–25:00)

---

## Adaptation à 20 minutes
- Fusionner les slides 2 et 3 (−1 min) et les slides 5 et 6 (−1,5 min, garder seulement l'exemple T1/T2).
- Démo réduite à 4 min : étapes 2, 3 et 4 seulement ; l'exploration est montrée sur la slide 11 (−2 min).
- Code : un seul extrait, `term_contributions` (−1,5 min).

## Adaptation à 30 minutes
- Ajouter l'**expérience B** en direct (p07/p25 = 0,271 > p01/p04 = 0,177) après la slide 6 (+2 min).
- Démo complète avec l'**expérience D** à 50 % (+1,5 min).
- Montrer l'onglet « Ouvrir l'algorithme » en entier, y compris la matrice complète (+1,5 min).
- Slide supplémentaire « Contenu vs collaboratif vs hybride » avec un petit exemple de matrice utilisateurs × posts (+1 min).

## Conseils de forme
- Répartition : A = théorie, M = démo et code, avec une alternance claire et annoncée.
- Même charte que l'application (dégradé sombre, accent indigo, une couleur par thème).
- Une idée par slide, un encadré « À retenir » par partie.
- Ne jamais lire la slide ; montrer du doigt la valeur numérique quand on la cite.
