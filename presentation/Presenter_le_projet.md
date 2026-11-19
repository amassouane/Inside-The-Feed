# Présenter le projet pas à pas : NLP + recommandation

Fiche de révision à garder à côté des diapos (`presentation/Presentation_InsideTheFeed.html`).
Pour chaque partie : **l'idée** (à comprendre), **ce qu'on dit**, **ce qu'on montre** (diapo, application, code)
et **le fichier source** (chemin + ligne).

- **A** = MASSOUANE Abdelati (théorie) · **M** = MOUATE Alaa Eddine (démo et code)
- Chemins relatifs au dossier du projet `~/Desktop/NLP_RECOMM/`. Ouvrir un fichier à une ligne dans VS Code : `⌘P` puis `model.py:64`.
- Chaque diapo suit le même schéma : un titre, une définition, 3 ou 4 puces qui apparaissent une par une (`→`), puis un encadré **💡 À retenir**. Notes orales : touche `N`.
- Versions PDF : `presentation/Presentation_InsideTheFeed.pdf` (diapos), `presentation/Guide_Presentation_InsideTheFeed.pdf` (guide), `tp/TP_InsideTheFeed.pdf` (TP).

---

## Vue d'ensemble : la chaîne complète

```
data/posts.json
  │  ① build_document      recommender/preprocessing.py:40   titre + description + hashtags
  ▼
texte brut
  │  ② preprocess          recommender/preprocessing.py:63   minuscules, mots, mots vides
  ▼
tokens
  │  ③ make_vectorizer     recommender/model.py:19           TF-IDF + normalisation L2
  ▼
matrice 40 × 564   ──────────────┐
  │  ④ build_profile        model.py:64                      moyenne des posts aimés
  ▼                              │
profil utilisateur               │
  │  ⑤ similarity_scores    model.py:81                      cosinus profil ↔ chaque post
  │     term_contributions  model.py:91                      explication mot par mot
  ▼                              │
scores                           │
  │  ⑥ build_feed           recommender/feed.py:92           classement + exploration
  ▼
feed affiché               app.py (Streamlit)
```

**Partie NLP** = étapes ① à ③ (le texte devient des nombres).
**Partie recommandation** = étapes ④ à ⑥ (les nombres deviennent un feed).
Moyen mnémotechnique : **Texte → Tokens → Poids → Profil → Score → Feed**.

---

## Partie 0 · Contexte (diapos 1–4, A, 3 min)

**Idée** : un feed est un problème de **tri**. Il y a 40 posts et 8 places à l'écran. Pour trier des textes, il faut pouvoir les comparer, donc les transformer en nombres.

**Étapes**
1. Diapo 1 : se présenter, annoncer le sujet en une phrase.
2. Diapo 2 : 40 → 8, puis lire la **problématique** : *comment transformer des textes et des likes en un feed personnalisé et explicable ?*
3. Diapo 3 : annoncer le plan et le partage (« je fais la théorie, Alaa Eddine la démo et le code »).
4. Diapo 4 : trois familles. Contenu = « ça ressemble à ce que j'aime ». Collaboratif = « aimé par ceux qui me ressemblent ». Hybride = les deux. **Nous faisons le contenu, car il est explicable.**

**Source** : `data/posts.json` (40 posts fictifs : `id`, `auteur`, `titre`, `description`, `hashtags`, `categorie`).

---

# PARTIE NLP : du texte au vecteur

## Étape ① · Le texte analysé (diapos 5–6, A)

**Idée** : le modèle ne lit **que le texte** (titre + description + hashtags). La catégorie n'est jamais utilisée dans le calcul.

**Étapes**
1. Diapo 5 : sans like, il n'y a pas de profil (**cold start**), donc on affiche un post par thème, sans score.
2. Diapo 6 : présenter la chaîne en 6 étapes. C'est la carte de toute la suite.

**Source**
```python
# recommender/preprocessing.py:40
def build_document(post):
    return " ".join([post["titre"], post["description"], " ".join(post["hashtags"])])
```
**Test** : `test_categorie_absente_du_texte_analyse` (`tests/test_recommender.py:32`).

---

## Étape ② · Prétraitement : texte → tokens (diapo 7, A)

**Idée** : garder seulement les mots **porteurs de sens**. Les mots vides (« le », « de », « au ») sont partout et ne distinguent aucun post.

**Ce qui est fait, dans l'ordre**
1. `text.lower()` : tout en minuscules.
2. Regex `[a-zàâäçéèêëîïôöùûüÿœæ]+` : on garde les suites de lettres. Ponctuation, chiffres, `#` et apostrophes servent de séparateurs (`#football` → `football`, `l'équipe` → `équipe`).
3. On garde les tokens de 2 lettres ou plus.
4. On retire les mots de `data/stopwords_fr.txt`.

**Chiffre à citer** : p01 → **50 tokens bruts → 29 conservés**.
**Limite à annoncer** : pas de lemmatisation, donc `joueur` ≠ `joueurs`.

**À montrer dans l'application** : onglet 🔬 *Ouvrir l'algorithme*, bloc **② Tokens** (`app.py:248`) : les mots vides apparaissent barrés.

**Source**
| Fonction | Fichier:ligne | Rôle |
|---|---|---|
| `TOKEN_PATTERN` | `recommender/preprocessing.py:17` | la regex |
| `tokenize` | `recommender/preprocessing.py:48` | minuscules + découpage |
| `remove_stopwords` | `recommender/preprocessing.py:57` | filtre des mots vides |
| `preprocess` | `recommender/preprocessing.py:63` | les deux à la suite |

**Test** : `test_preprocess_minuscules_stopwords_hashtags` (`tests/test_recommender.py:27`).

---

## Étape ③ · TF-IDF : tokens → vecteur (diapo 8, A)

**Idée** : chaque mot reçoit un **poids**.
- **tf** = « ce mot compte **ici** » (nombre d'occurrences dans le post).
- **idf** = « ce mot est rare **ailleurs** » (un mot présent partout aide peu à distinguer).

**Formules exactes**
```
tf(t, d) = nombre d'occurrences de t dans d
idf(t)   = ln( (1 + n) / (1 + df(t)) ) + 1          n = 40 posts, df = nb de posts contenant t
poids    = tf × idf, puis division par la norme L2   → chaque vecteur a une longueur 1
```

**Chiffres à citer**
- Vocabulaire de **564 termes** → un post = un vecteur de 564 nombres, dont **3,3 %** seulement sont non nuls.
- p01 : `derby` 0,362 · `victoire` 0,362 · `match` 0,263 · `supporters` 0,263 · `football` 0,109.
- `football` a un idf de 2,41 (présent dans beaucoup de posts) et `derby` un idf de 4,02 (un seul post).

**À montrer dans l'application** : onglet 🔬, bloc **③ Poids TF-IDF** (`app.py:260`) ; onglet 🧪 → **A** pour l'exemple à 3 textes.

**Source**
```python
# recommender/model.py:19
def make_vectorizer():
    return TfidfVectorizer(
        analyzer=preprocess,   # notre prétraitement remplace celui de scikit-learn
        use_idf=True, smooth_idf=True, sublinear_tf=False, norm="l2")
```
- La matrice est construite dans `FeedModel.__post_init__` (`recommender/model.py:36`) : `fit_transform` sur les 40 documents.
- **Point fort à dire** : le **même** `preprocess` sert à afficher les tokens et à calculer les vecteurs.

**Tests** : `test_formule_idf_documentee` (`:43`), `test_lignes_normalisees` (`:38`) dans `tests/test_recommender.py`.

---

## Étape ③ bis · Cosinus : comparer deux vecteurs (diapos 9–10, A)

**Idée** : deux textes qui partagent des mots importants **pointent dans la même direction**. Aucun mot commun, angle droit, cosinus = 0.

**Formule** : comme les vecteurs ont une longueur 1, `cos(u, v) = Σ u[t] × v[t]`, une simple somme de produits.

**Exemple à savoir refaire au tableau (expérience A, diapo 10)**
| | football | match | stade | voyage | barcelone |
|---|---|---|---|---|---|
| T1 « Le match de football au stade » | 0,6228 | 0,6228 | 0,4736 | 0 | 0 |
| T2 « Voyage au stade de Barcelone » | 0 | 0 | 0,4736 | 0,6228 | 0,6228 |

1. idf de `stade` (2 textes sur 3) = ln(4/3) + 1 = **1,2877** ; idf des autres (1 texte) = ln(4/2) + 1 = **1,6931**.
2. Norme de T1 = √(1,6931² + 1,6931² + 1,2877²) = 2,7187, donc 1,6931 / 2,7187 = 0,6228 et 1,2877 / 2,7187 = 0,4736.
3. cos(T1, T2) = 0,4736 × 0,4736 = **0,224** (seul `stade` est commun). cos(T1, T3) = **0**.

**Source** : `FeedModel.cosine_between` (`recommender/model.py:85`).
**Test** : `test_exemple_numerique_de_la_doc` (`tests/test_recommender.py:49`).

> **Passage de parole (A → M)** : « Le texte est devenu un vecteur. Mais comment l'utilisateur devient-il un vecteur, et comment passe-t-on des scores à un feed ? Alaa Eddine va vous le montrer. »

---

# PARTIE RECOMMANDATION : du vecteur au feed

## Étape ④ · Le profil utilisateur (diapo 11, M)

**Idée** : l'utilisateur devient un **« post moyen »** de ce qu'il aime. Il vit dans le même espace que les posts, donc on peut le comparer à n'importe quel post.

**Formule** : `profil = moyenne des vecteurs aimés`, puis division par sa norme. Sans like → `None` (cold start).

**Chiffre à citer** : likes p01, p02, p03 → `but`, `match`, `supporters` dominent le profil.

**À montrer dans l'application** : barre latérale, bouton **⚽ Fan de football** ; onglet 🔬, bloc **④ Profil utilisateur** (`app.py:276`).

**Source**
```python
# recommender/model.py:64-74
def build_profile(self, liked_ids):
    if not liked_ids:
        return None                                   # cold start
    rows = [self.index[pid] for pid in liked_ids]
    mean = np.asarray(self.matrix[rows].mean(axis=0)).ravel()
    norm = np.linalg.norm(mean)
    return mean / norm if norm > 0 else None
```
**Tests** : `test_profil_vide` (`:62`), `test_profil_normalise_et_moyenne` (`:67`).

---

## Étape ⑤ · Le score et son explication (diapos 12–13, M)

**Idée** : score = cosinus entre le profil et chaque post. Chaque mot commun apporte un **morceau** du score (poids dans le profil × poids dans le post). En additionnant les morceaux, on retrouve exactement le score : **c'est explicable**.

**Étapes**
1. Diapo 12 : p04 est n°1 avec **0,148** = supporters 0,059 + match 0,029 + stade 0,022 + football 0,020 + équipe 0,019.
2. Diapo 13 : les **pâtes** (p18) sont 8ᵉ à cause du seul mot `rapide` (0,029). C'est de la **polysémie** : le modèle compte des mots, il ne comprend pas le sens.

**À dire** : « score de similarité », **jamais** « probabilité d'aimer ».

**À montrer dans l'application** : onglet 🔬, *Publication à suivre* = p04 puis p18, bloc **⑤ Score de similarité** (`app.py:289`).

**Source**
```python
# recommender/model.py:81
def similarity_scores(self, profile):
    return cosine_similarity(profile.reshape(1, -1), self.matrix).ravel()

# recommender/model.py:91
def term_contributions(self, profile, post_id):
    post = self.post_vector(post_id)
    products = profile * post            # produit terme à terme = le « pourquoi »
    shared = np.flatnonzero(products)    # seuls les mots communs
    ...                                  # trié par contribution décroissante
```
**Tests** : `test_cosinus_egal_produit_scalaire` (`:75`), `test_contributions_somment_au_score` (`:81`), `test_etape3_explication_p04` (`tests/test_scenarios.py:26`).

---

## Étape ⑥ · Le classement (diapo 14, M)

**Idée** : on prend tous les posts **non aimés** et on les trie par score décroissant (égalité → plus petit identifiant). On affiche les 8 premiers.
Le profil est une moyenne : avec 4 likes, chaque like pèse 25 %. **Un seul like peut donc tout déplacer.**

**Chiffres à citer (ajout du like p10, road trip au Maroc)**
- p09 Barcelone **▲3** : de la 5ᵉ à la 2ᵉ place (football + voyage).
- p15 Jemaa el-Fna et p14 billets d'avion **entrent** ; p05 et p18 **sortent**.
- Le mot rare `désert` (idf 4,02) passe en tête du profil.

**À montrer dans l'application** : bouton **⚽ + ✈️ Football puis voyage** ; dans le feed, les badges ▲ et 🆕.

**Source**
```python
# recommender/feed.py:55
def rank_by_similarity(model, liked_ids):
    profile = model.build_profile(liked_ids)
    if profile is None:
        return []
    scores = model.similarity_scores(profile)
    liked = set(liked_ids)
    ranking = [(pid, float(scores[i])) for i, pid in enumerate(model.ids) if pid not in liked]
    return sorted(ranking, key=lambda x: (-x[1], x[0]))
```
**Tests** : `test_classement_decroissant` (`:116`), `test_feed_sans_doublon_ni_post_aime` (`:108`), `test_etape4_ajout_voyage` (`tests/test_scenarios.py:31`).

---

## Étape ⑥ bis · Cold start et exploration (diapos 5 et 15, M)

**Idée** : ce ne sont **pas** des calculs NLP mais des **règles produit**, séparées et déterministes. Elles ne modifient jamais les scores.

**Cold start (sans like)** : un post par thème à tour de rôle, dans l'ordre fixe football → voyage → cuisine → gaming → technologie → fitness. Résultat : p01, p09, p17, p08, p22, p29, p02, p10.

**Exploration (contre la surspécialisation)**
1. `k = arrondi(8 × proportion)` places réservées (25 % → **2**).
2. Thèmes absents du top 8 : ici **cuisine** et **fitness**.
3. On prend le meilleur post non aimé de chaque thème absent, à tour de rôle : **p18** (0,026) et **p36** (0,013).
4. On les insère tous les `8 // k` rangs : positions **4 et 8**.

**À montrer dans l'application** : curseur *Part du feed réservée à l'exploration* à 25 % dans la barre latérale ; badge 🧭.

**Source**
| Fonction | Fichier:ligne | Rôle |
|---|---|---|
| `initial_feed` | `recommender/feed.py:38` | feed sans like |
| `exploration_slots` | `recommender/feed.py:69` | k = arrondi(8 × p) |
| `pick_exploration` | `recommender/feed.py:74` | choix des posts d'exploration |
| `build_feed` | `recommender/feed.py:92` | **point d'entrée unique** : cold start, classement, exploration |

**Tests** : `test_feed_initial_equilibre_deterministe` (`:90`), `test_exploration_themes_absents_et_scores_inchanges` (`:129`), `test_etape5_exploration` (`tests/test_scenarios.py:39`).

---

## Partie démo en direct (diapo 16, M aux commandes, A commente, 4 min)

Avant : `cd ~/Desktop/NLP_RECOMM && source .venv/bin/activate && streamlit run app.py`, puis http://localhost:8501 → **🔄 Réinitialiser** → **🎤 Mode présentation**.

| # | Clic | Ce qu'on voit | Partie illustrée |
|---|---|---|---|
| 1 | Étape 1 du parcours guidé | feed p01, p09, p17… badge « non personnalisé » | cold start |
| 2 | Suivant ▶ | p04 n°1 (0,148) … p18 pâtes 8ᵉ | profil + score |
| 3 | Onglet 🔬, p04 puis p18 | contributions mot par mot ; p18 = « rapide » | explication |
| 4 | Onglet 📱, Suivant ▶ | p09 ▲3, p15 et p14 🆕 | classement |
| 5 | Suivant ▶ | p18 et p36 🧭 en positions 4 et 8 | exploration |
| 6 | Onglet 📚 | cos(p01, p07) = 0 | limites |

Si un clic tourne mal : **« ▶ Appliquer cette étape »** recharge l'état exact. Si l'application plante, les diapos 12–15 montrent déjà les mêmes résultats.

---

## Partie code (diapos 17–18, M, 3 min)

**Idée** : le moteur est **petit**, **séparé** de l'interface, et **ce qu'on montre est ce qui s'exécute**.

**Architecture à montrer dans l'explorateur de VS Code**
```
recommender/      le CERVEAU : calculs, n'importe jamais Streamlit
  preprocessing.py   étapes ① ②
  model.py           étapes ③ ④ ⑤
  feed.py            étape ⑥
  scenarios.py       scénarios de démo, expériences A–D, parcours guidé
app.py            la VITRINE : affichage Streamlit (4 onglets)
tests/            44 tests
```

**Ordre de présentation (4 extraits)**
1. `recommender/preprocessing.py:63` `preprocess`, puis `recommender/model.py:22` `analyzer=preprocess` : un seul code pour l'affichage et le calcul.
2. `recommender/model.py:64` `build_profile` : une moyenne puis une division.
3. `recommender/model.py:98` `products = profile * post` : tout le « pourquoi ».
4. `recommender/feed.py:92` `build_feed` : la frontière entre le NLP (scores) et la règle d'affichage (exploration).

**Liens interface → moteur dans `app.py`**
| Ligne | Ce que c'est |
|---|---|
| `app.py:32` | `get_model()` : le TF-IDF est calculé **une seule fois** (`st.cache_resource`) |
| `app.py:48` | `current_feed()` : appelle `build_feed` à chaque affichage |
| `app.py:57` | `toggle_like` : un clic sur ♡ ajoute ou retire un like |
| `app.py:81` | `show_code` : affiche le code source **réel** avec `inspect.getsource` |
| `app.py:159` | les 4 onglets : Feed · Ouvrir l'algorithme · Expériences · Comprendre & limites |
| `app.py:241–304` | les blocs ① à ⑥ de l'onglet 🔬 |

**Validation (diapo 18)** : `python -m pytest -q` → **44 passed** en environ 4 s.
`python scripts/verifier_resultats.py` recalcule tous les chiffres de la présentation.

> **Passage de parole (M → A)** : « Le moteur fonctionne et il est vérifié. Mais il a des limites, et Abdelati va vous les présenter. »

---

## Partie limites (diapos 19–20, A, 2 min)

**Idée commune** : le modèle ne compare que des **mots identiques**. Il ignore synonymes, sens et contexte, et ne regarde que le passé.

| Limite | Preuve dans notre démo | Amélioration possible |
|---|---|---|
| Synonymes | « football » ≠ « foot » : cos(p01, p07) = **0** | embeddings sémantiques, dictionnaire de synonymes |
| Polysémie | « rapide » fait entrer des pâtes | embeddings contextuels |
| Mots ≠ thème | foot entre amis / e-sport = **0,271** > deux posts football = **0,177** | n-grammes, embeddings |
| Surspécialisation | le feed se resserre sur les likes passés | exploration, système hybride |
| Pas de lemmatisation | `joueur` ≠ `joueurs` | lemmatisation |

**Ce que la démo prouve / ne prouve pas** : elle **illustre** un mécanisme réel et explicable. Elle ne prouve **rien** sur TikTok ou Instagram, ni sur les bulles de filtre (un utilisateur fictif, 40 posts).

> **Passage de parole (A → M)** : « Alaa Eddine, pour conclure. »

---

## Conclusion (diapos 21–22, M)

> « TF-IDF transforme le texte en vecteurs, le cosinus compare, le feed classe et explore.
> Un feed n'est pas magique : c'est un calcul, et ce calcul a des limites. »

---

## Récapitulatif d'une ligne par étape

| Étape | Idée en une phrase | Fichier:ligne |
|---|---|---|
| ① Texte | Le modèle lit titre + description + hashtags, jamais la catégorie. | `preprocessing.py:40` |
| ② Tokens | On garde les mots porteurs de sens. | `preprocessing.py:63` |
| ③ TF-IDF | Fréquent ici × rare ailleurs = mot important. | `model.py:19` |
| ③ bis Cosinus | Mêmes mots importants = même direction. | `model.py:85` |
| ④ Profil | L'utilisateur = la moyenne de ce qu'il aime. | `model.py:64` |
| ⑤ Score | Somme des produits des mots communs, donc explicable. | `model.py:81`, `:91` |
| ⑥ Classement | Posts non aimés triés par score. | `feed.py:55` |
| ⑥ bis Exploration | Règle produit : des places pour les thèmes absents. | `feed.py:92` |
| Interface | `app.py` affiche, `recommender/` calcule. | `app.py:48` |
