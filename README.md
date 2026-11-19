# 📡 Inside the Feed

**Démonstrateur interactif d'un moteur de recommandation basé sur le contenu.**
Inside the Feed simule un mini réseau social et montre, étape par étape, comment des **textes**
et des **likes** deviennent un **feed personnalisé** grâce au NLP : prétraitement, vecteurs TF-IDF,
profil utilisateur et similarité cosinus.

⚠️ Les 40 publications de `data/posts.json` sont **entièrement fictives**.
Ce simulateur ne reproduit **pas** l'algorithme de TikTok, d'Instagram ni d'aucune plateforme réelle :
il illustre un mécanisme, il ne prouve rien sur les systèmes réels.

---

## Sommaire

1. [Principe](#principe)
2. [Le pipeline de recommandation](#le-pipeline-de-recommandation)
3. [Les deux interfaces](#les-deux-interfaces)
4. [Scénarios, expériences et parcours guidé](#scénarios-expériences-et-parcours-guidé)
5. [Données](#données)
6. [Installation et lancement](#installation-et-lancement)
7. [Tests et vérifications](#tests-et-vérifications)
8. [Arborescence](#arborescence)
9. [Documents fournis](#documents-fournis)
10. [Limites](#limites)

---

## Principe

L'utilisateur voit un feed de **8 publications**. Chaque fois qu'il clique sur **♡ J'aime** :

1. le texte des posts aimés est transformé en vecteurs TF-IDF ;
2. ces vecteurs sont moyennés pour former un **profil** (l'utilisateur devient un vecteur) ;
3. chaque post non aimé reçoit un **score** = cosinus(profil, post) ;
4. le feed est re-trié par score décroissant, avec en option une part d'**exploration**.

Toutes les étapes intermédiaires (tokens, poids, profil, contribution de chaque mot au score) sont
affichées à l'écran, avec le fichier et la fonction Python qui les calculent.

## Le pipeline de recommandation

```
titre + description + hashtags                         recommender/preprocessing.py
   → minuscules, découpage en mots, mots vides retirés
   → vecteurs TF-IDF ajustés sur les 40 posts           recommender/model.py
   → profil = moyenne des posts aimés, normalisée L2    recommender/model.py
   → similarité cosinus profil ↔ chaque post            recommender/model.py
   → classement des posts non aimés + exploration       recommender/feed.py
   → affichage                                          app.py / app_complet.py, ui_style.py
```

### 1. Prétraitement — `recommender/preprocessing.py`
- Document analysé = **titre + description + hashtags**. La catégorie n'est **pas** lue (elle sert
  uniquement à l'affichage et à l'exploration).
- Passage en minuscules, tokenisation par expression régulière (lettres accentuées comprises,
  tokens d'au moins 2 lettres).
- Suppression des mots vides à partir d'une liste locale (`data/stopwords_fr.txt`).

### 2. Vectorisation TF-IDF — `recommender/model.py`
`TfidfVectorizer` de scikit-learn, avec notre prétraitement comme `analyzer` et des paramètres explicites :

```
tf(t, d) = nombre d'occurrences de t dans d          (sublinear_tf=False)
idf(t)   = ln((1 + n) / (1 + df(t))) + 1              (smooth_idf=True)
vecteur  = tf × idf, puis normalisation L2            (norm="l2")
```

### 3. Profil utilisateur
Profil = **moyenne des vecteurs des posts aimés**, puis normalisation L2.
Sans like, il n'y a pas de profil : c'est le **cold start**.

### 4. Score de similarité
Score = **similarité cosinus** entre le profil et chaque publication. Les vecteurs étant normalisés,
le score se décompose exactement en une somme : `cos = Σ profil[t] × post[t]` sur les termes communs.
L'application affiche ces contributions pour **expliquer** chaque recommandation. C'est une
similarité, pas une probabilité.

### 5. Construction du feed — `recommender/feed.py`
- **Sans like** : feed initial équilibré et déterministe, un post par thème à tour de rôle
  (football, voyage, cuisine, gaming, technologie, fitness). Aucun score, aucune personnalisation.
- **Avec likes** : tous les posts non aimés sont triés par score décroissant (l'identifiant
  départage les égalités), les 8 premiers sont affichés.
- **Exploration** : une règle **séparée du modèle NLP** réserve `arrondi(8 × proportion)` places
  aux thèmes absents du top 8. Elle prend, à tour de rôle, le meilleur post restant de chaque thème
  absent. Les scores ne sont jamais modifiés ; les posts concernés portent le badge « exploration ».

## Les deux interfaces

### `app.py` — vue simple (une page)
- À gauche, le **feed** : cartes visuelles (dégradé + emoji par thème), rang, score, badges
  *nouveau* / *▲ montée*, bouton **♡ J'aime**.
- À droite, **« Ce que le moteur vient de faire »** après chaque like : texte du post, tokens (mots
  vides barrés), vecteur TF-IDF, profil, décomposition du score du n° 1, posts qui entrent ou sortent
  du feed.
- Interrupteur **Exploration 25 %** et bouton **Réinitialiser**.

```bash
streamlit run app.py
```

### `app_complet.py` — version complète
- **Barre latérale** : mode présentation, boutons de scénarios, curseur d'exploration (0 à 50 %),
  liste des likes (retrait possible), réinitialisation.
- **📱 Feed** : indicateurs (likes, personnalisé ou non, places d'exploration, taille du vocabulaire),
  feed complet, inspection de la matrice TF-IDF entière (40 posts × termes).
- **🔬 Ouvrir l'algorithme** : suivi pas à pas d'une publication choisie, du texte brut jusqu'au score,
  avec le code source des fonctions concernées.
- **🧪 Expériences A–D** : voir ci-dessous.
- **📚 Comprendre & limites** : rappel des formules, de ce que la démo montre et de ce qu'elle ne montre pas.
- **🎤 Mode présentation** : police agrandie et parcours guidé en 6 étapes (« à dire / à observer »).

```bash
streamlit run app_complet.py
```

## Scénarios, expériences et parcours guidé

Tout est figé dans `recommender/scenarios.py` pour que la démonstration soit reproductible, et les
effets annoncés sont vérifiés par `tests/test_scenarios.py`.

| Scénario | Likes | Ce qu'on observe |
|---|---|---|
| 🧊 Aucun like | — | Cold start : feed non personnalisé |
| ⚽ Fan de football | p01, p02, p03 | p04 (Coupe d'Afrique) passe en tête |
| ⚽ + ✈️ Football puis voyage | + p10 | p09 (Barcelone : football + voyage) monte de la 5ᵉ à la 2ᵉ place |
| 🧭 Exploration 25 % | mêmes likes | 2 places sur 8 pour des thèmes absents (cuisine, fitness) |

| Expérience | Objectif |
|---|---|
| **A · Textes → vecteurs** | Vectoriser trois textes courts modifiables, seuls, avec le même vectoriseur |
| **B · Cosinus entre deux posts** | Comparer deux publications au choix (ex. « football » vs « foot » : TF-IDF ne voit que les mots identiques) |
| **C · Football puis voyage** | Voir le profil et le feed se déplacer quand un nouvel intérêt apparaît |
| **D · Avec / sans exploration** | Comparer côte à côte le feed à 0 % et à X % d'exploration |

## Données

- `data/posts.json` : **40 publications fictives** réparties en 6 thèmes : voyage (8), football (7),
  technologie (7), gaming (6), cuisine (6) et fitness (6). Champs : `id`, `auteur`, `titre`,
  `description`, `hashtags`, `categorie`.
- `data/stopwords_fr.txt` : liste locale de mots vides français (un mot par ligne).

Aucune API, aucun compte, aucune base de données : tout fonctionne **hors ligne**, en local.

## Installation et lancement

Python 3.10 ou plus récent (développé avec Python 3.13).

```bash
git clone https://github.com/amassouane/Inside-The-Feed.git
cd Inside-The-Feed
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt pytest
streamlit run app_complet.py      # ou : streamlit run app.py
```

Puis ouvrir **http://localhost:8501**. Le serveur n'écoute que sur `localhost` et la télémétrie
Streamlit est désactivée (`.streamlit/config.toml`).

Dépendances : `streamlit`, `scikit-learn`, `numpy`, `pandas` (versions testées : streamlit 1.66.1,
scikit-learn 1.9.1).

## Tests et vérifications

```bash
python -m pytest -q                      # calculs, feed, exploration, scénarios, interfaces (AppTest)
python scripts/verifier_resultats.py     # recalcule tous les chiffres des scénarios
```

- `tests/test_recommender.py` : prétraitement, TF-IDF, profil, cosinus, contributions, feed, exploration.
- `tests/test_scenarios.py` : les effets annoncés dans les scénarios et le parcours guidé sont bien réels.
- `tests/test_app_simple.py`, `tests/test_app.py` : interfaces testées sans navigateur via
  `streamlit.testing.v1.AppTest` (vrais clics sur les vrais boutons).

## Arborescence

```
app.py                      Interface simple (une page : feed + étapes du moteur)
app_complet.py              Interface complète (4 onglets, scénarios, mode présentation)
ui_style.py                 CSS, visuels locaux (dégradés + emojis), HTML des cartes
recommender/
  preprocessing.py          Texte → tokens (minuscules, regex, mots vides)
  model.py                  TF-IDF, profil, cosinus, contributions des termes
  feed.py                   Feed initial, classement, règle d'exploration
  scenarios.py              Scénarios de démo, expériences A–D, parcours guidé
data/
  posts.json                40 publications fictives (6 thèmes)
  stopwords_fr.txt          Liste locale de mots vides
tests/                      pytest (calculs, scénarios, interfaces)
scripts/verifier_resultats.py
docs/                       Mécanismes, guide du code, démo, questions/réponses
```

## Documentation

| Document | Contenu |
|---|---|
| `docs/mecanismes.md` | Les formules et un exemple numérique minuscule |
| `docs/guide_code.md` | L'ordre de lecture du code |

**Par où commencer ?** `docs/mecanismes.md` → `docs/guide_code.md`.

## Limites

- 40 posts fictifs et un seul utilisateur : le système illustre un mécanisme, sans données réelles.
- Approche **purement basée sur le contenu** : pas de filtrage collaboratif, pas de signaux
  d'engagement (temps de visionnage, partages…), pas d'apprentissage.
- TF-IDF ne comprend pas le sens : « football » et « foot » sont des mots différents, et un mot isolé
  comme « rapide » peut faire remonter un post hors sujet.
- Aucune conclusion sur TikTok, Instagram ou les bulles de filtre ne peut être tirée de cette démo.
