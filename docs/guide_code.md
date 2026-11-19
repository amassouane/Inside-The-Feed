# Guide de lecture du code

Environ 400 lignes pour les calculs (`recommender/`) et 600 lignes pour l'interface (`app.py`, `ui_style.py`). Les calculs (`recommender/`) n'importent jamais Streamlit :
on peut les tester et les expliquer sans interface.

## Ordre de lecture conseillé

| # | Fichier | Pourquoi le lire | Durée |
|---|---|---|---|
| 1 | `data/posts.json` | Voir la forme d'une publication (id, titre, description, hashtags, catégorie) | 2 min |
| 2 | `recommender/preprocessing.py` | Texte → tokens | 3 min |
| 3 | `recommender/model.py` | TF-IDF, profil, cosinus, explication | 8 min |
| 4 | `recommender/feed.py` | Feed initial, classement, exploration | 6 min |
| 5 | `recommender/scenarios.py` | Scénarios de démo et parcours guidé | 2 min |
| 6 | `app.py` | Comment l'interface appelle les fonctions | 10 min |
| 7 | `tests/` | Ce qui est garanti | 5 min |

## Fonctions clés

### `preprocessing.py`
- **`build_document(post)`** : colle titre, description et hashtags. La catégorie est volontairement exclue :
  le modèle ne doit apprendre que du texte.
- **`tokenize(text)`** : `lower()` puis une expression régulière qui garde les suites de lettres accentuées.
- **`remove_stopwords(tokens)`** : filtre avec `data/stopwords_fr.txt`, chargé une fois (`lru_cache`).
- **`preprocess(text)`** : la composition des deux. Elle est passée telle quelle à scikit-learn
  (`analyzer=preprocess`) : **le même code** sert à l'affichage des tokens et au calcul.

### `model.py`
- **`make_vectorizer()`** : `TfidfVectorizer` avec tous les paramètres explicites
  (`smooth_idf=True`, `sublinear_tf=False`, `norm="l2"`), ceux de `docs/mecanismes.md`.
- **`FeedModel`** (dataclass) : à la construction, il vectorise les 40 documents.
  - `matrix` : matrice creuse 40 × 564, lignes de norme 1 ;
  - `index` / `by_id` : passer d'un identifiant à une ligne ou à un post.
- **`build_profile(liked_ids)`** : moyenne des lignes aimées puis division par la norme ; `None` sans like.
- **`similarity_scores(profile)`** : `cosine_similarity(profil, matrice)` → un score par post.
- **`cosine_between(a, b)`** : cosinus entre deux posts (expérience B).
- **`term_contributions(profile, post_id)`** : `profile * post` terme à terme ; les produits non nuls
  sont l'explication du score, et leur somme est exactement le score.

### `feed.py`
- **`initial_feed(model)`** : tour de rôle sur les thèmes. Aucun appel au modèle NLP.
- **`rank_by_similarity(model, liked_ids)`** : exclut les posts aimés, trie par `(-score, id)`.
- **`exploration_slots(size, p)`** : `floor(size × p + 0,5)`.
- **`pick_exploration(...)`** : tour de rôle sur les thèmes absents, en prenant le meilleur post restant.
- **`build_feed(model, liked_ids, exploration)`** : **point d'entrée unique** utilisé par l'interface.
  Il renvoie un `FeedResult` (liste de `FeedItem(post_id, score, origine)` + thèmes du top et thèmes absents).

### `app.py`
- `get_model()` est mis en cache (`st.cache_resource`) : le TF-IDF est calculé une seule fois.
- L'état tient dans `st.session_state` : `likes`, `exploration_pct`, `prev_feed` (pour afficher ▲▼🆕),
  `tour_step`, `presentation`.
- Les boutons utilisent des **callbacks** (`toggle_like`, `apply_scenario`, `reset`, `go_step`) :
  l'état est modifié avant le réaffichage, donc le feed se reclasse immédiatement.
- `show_code(fn)` affiche le code source **réel** des fonctions avec `inspect.getsource` :
  ce qui est montré à l'écran est ce qui s'exécute.

## Montrer le code pendant la présentation (≈ 3 min)

1. `preprocess`, en 4 lignes, avec `analyzer=preprocess` dans `make_vectorizer`.
2. `build_profile` : une moyenne puis une division.
3. `term_contributions` : `profile * post`, c'est tout le « pourquoi ».
4. `build_feed` : la frontière entre le NLP (scores) et la règle d'affichage (exploration).

Astuce : dans l'onglet **Ouvrir l'algorithme**, chaque étape a un bouton « 💻 Voir le code ».
