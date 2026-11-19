# Mécanismes — formules réellement employées

Ce document décrit **exactement** ce que calcule le code, avec les paramètres utilisés.
Chaque section renvoie à la fonction correspondante.

---

## 1. Prétraitement — `recommender/preprocessing.py`

| Étape | Fonction | Règle |
|---|---|---|
| Texte analysé | `build_document(post)` | `titre + " " + description + " " + hashtags`. **La catégorie n'est pas incluse.** |
| Minuscules + tokens | `tokenize(text)` | `text.lower()`, puis regex `[a-zàâäçéèêëîïôöùûüÿœæ]+` ; tokens de 2 lettres ou plus |
| Mots vides | `remove_stopwords(tokens)` | Retire les mots de `data/stopwords_fr.txt` (liste locale écrite à la main) |
| Chaîne complète | `preprocess(text)` | `remove_stopwords(tokenize(text))` |

Conséquences visibles :
- ponctuation, chiffres, apostrophes et `#` séparent les mots : `l'équipe` → `équipe`, `#football` → `football` ;
- pas de lemmatisation ni de racinisation : `joueur` ≠ `joueurs`, `maroc` ≠ `marocain` ;
- les nombres écrits en lettres (`dix`, `trois`…) sont des mots vides : c'est un **choix du projet**,
  car `dix buts` et `dix minutes de yoga` créaient une similarité sans rapport avec le sens.

## 2. TF-IDF — `make_vectorizer()` dans `recommender/model.py`

```python
TfidfVectorizer(analyzer=preprocess, use_idf=True, smooth_idf=True, sublinear_tf=False, norm="l2")
```

Avec *n* = nombre de documents du corpus (40) et *df(t)* = nombre de documents contenant *t* :

```
tf(t, d)     = nombre d'occurrences de t dans d             (sublinear_tf=False : pas de log)
idf(t)       = ln( (1 + n) / (1 + df(t)) ) + 1              (smooth_idf=True)
w(t, d)      = tf(t, d) × idf(t)
x_d[t]       = w(t, d) / ‖w(·, d)‖₂                         (norm="l2")
```

Le vectoriseur est **ajusté sur les 40 posts** (`fit_transform` dans `FeedModel.__post_init__`) :
vocabulaire de **564 termes**, matrice 40 × 564 avec 735 valeurs non nulles (3,3 %).

Exemples d'idf sur le corpus : `désert` 4,020 (1 post) · `supporters` 2,922 · `voyage` 2,516 · `football` 2,411.
Plus un mot est répandu, plus son idf est faible.

## 3. Profil utilisateur — `FeedModel.build_profile(liked_ids)`

```
moyenne  = (1 / |L|) × Σ_{d ∈ L} x_d          (L = posts aimés)
u        = moyenne / ‖moyenne‖₂
```

Sans like, la fonction renvoie `None` (cold start).

## 4. Score de similarité — `FeedModel.similarity_scores(profile)`

```
score(u, d) = cos(u, x_d) = (u · x_d) / (‖u‖ × ‖x_d‖) = u · x_d      car ‖u‖ = ‖x_d‖ = 1
```

Calculé avec `sklearn.metrics.pairwise.cosine_similarity`. Comme tous les poids sont positifs,
le score est compris entre 0 et 1. **Ce n'est pas une probabilité d'aimer.**

## 5. Explication — `FeedModel.term_contributions(profile, post_id)`

Le cosinus est une somme sur les termes :

```
score(u, d) = Σ_t  u[t] × x_d[t]
```

Seuls les termes présents **à la fois** dans le profil et dans le post ont une contribution non nulle.
La fonction renvoie ces termes triés par contribution ; leur somme est **exactement** le score
(vérifié par `test_contributions_somment_au_score`).

## 6. Classement — `rank_by_similarity(model, liked_ids)` dans `recommender/feed.py`

Posts **non aimés**, triés par score décroissant ; à égalité, par identifiant croissant.
Le feed affiche les **8** premiers (`FEED_SIZE = 8`).

## 7. Feed initial — `initial_feed(model)`

Sans like : un post par thème à tour de rôle, dans l'ordre fixe
`football → voyage → cuisine → gaming → technologie → fitness`, le plus petit identifiant d'abord.
Résultat : p01, p09, p17, p08, p22, p29, p02, p10. **Aucun score, aucune personnalisation.**
Ici, la catégorie sert uniquement à équilibrer l'affichage.

## 8. Exploration — `exploration_slots`, `pick_exploration`, `build_feed`

Règle **séparée du modèle NLP** :

1. `k = arrondi(8 × proportion)` places réservées (25 % → 2, 50 % → 4).
2. Classement de pertinence initial = les 8 premiers posts par score (= le feed à 0 %).
3. Thèmes absents = thèmes qui n'apparaissent pas dans ces 8 posts.
4. On parcourt les thèmes absents dans l'ordre fixe et on prend, à tour de rôle,
   le **meilleur post non aimé** de chaque thème, jusqu'à *k* posts.
5. Les autres places reçoivent les meilleurs scores, sans doublon.
6. Les posts d'exploration sont insérés tous les `8 // nb_exploration` rangs (positions 4 et 8 pour 2 posts).
7. **Les scores ne sont jamais modifiés.** S'il n'y a aucun thème absent, aucune place n'est forcée.

---

## Exemple numérique minuscule (expérience A)

Trois textes, vectorisés **seuls** (*n* = 3) avec le même `make_vectorizer()` :

| Texte | Tokens après `preprocess` |
|---|---|
| T1 « Le match de football au stade » | match, football, stade |
| T2 « Voyage au stade de Barcelone » | voyage, stade, barcelone |
| T3 « Recette du tajine marocain » | recette, tajine, marocain |

**idf** : `stade` est dans 2 textes → ln(4/3) + 1 = **1,2877** ; tous les autres sont dans 1 texte → ln(4/2) + 1 = **1,6931**.

**T1** : poids bruts (1,6931 ; 1,6931 ; 1,2877), norme √(1,6931² + 1,6931² + 1,2877²) = 2,7187

| | football | match | stade | voyage | barcelone |
|---|---|---|---|---|---|
| T1 | **0,6228** | **0,6228** | **0,4736** | 0 | 0 |
| T2 | 0 | 0 | **0,4736** | **0,6228** | **0,6228** |

**Cosinus** : cos(T1, T2) = 0,4736 × 0,4736 = **0,2243** (seul `stade` est commun) ; cos(T1, T3) = **0**.

**Profil si l'on aime T1 et T2** : moyenne = (0,3114 ; 0,3114 ; 0,4736 ; 0,3114 ; 0,3114), norme 0,7824
→ profil = (0,398 ; 0,398 ; **0,6053** ; 0,398 ; 0,398). `stade`, commun aux deux likes, domine.
Score de T1 = 2 × 0,398 × 0,6228 + 0,6053 × 0,4736 = **0,7824** ; score de T3 = **0**.

Ces valeurs sont recalculées par `test_exemple_numerique_de_la_doc` et par `scripts/verifier_resultats.py`.

## Correspondance formule → code

| Formule | Fonction | Test |
|---|---|---|
| tokens | `preprocessing.preprocess` | `test_preprocess_minuscules_stopwords_hashtags` |
| idf lissé | `model.make_vectorizer` | `test_formule_idf_documentee` |
| ‖x_d‖ = 1 | `FeedModel.__post_init__` | `test_lignes_normalisees` |
| profil | `FeedModel.build_profile` | `test_profil_normalise_et_moyenne` |
| cos = produit scalaire | `FeedModel.similarity_scores` | `test_cosinus_egal_produit_scalaire` |
| Σ contributions = score | `FeedModel.term_contributions` | `test_contributions_somment_au_score` |
| classement | `feed.rank_by_similarity` | `test_classement_decroissant` |
| exploration | `feed.pick_exploration`, `feed.build_feed` | `test_exploration_*` |
