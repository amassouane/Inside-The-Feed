# TP — Inside the Feed : du texte au feed personnalisé

## 1. Objectifs

À la fin du TP, vous saurez :
- transformer un texte en tokens puis en vecteur TF-IDF ;
- calculer et interpréter une similarité cosinus ;
- expliquer comment un profil utilisateur est construit à partir de likes ;
- expliquer **pourquoi** un post est recommandé (contribution des termes) ;
- distinguer le **modèle** (scores) de la **règle d'affichage** (exploration) ;
- identifier les limites d'une recommandation basée sur le contenu.

## 2. Environnement

| Élément | Valeur |
|---|---|
| Langage | Python 3.10+ (testé avec 3.13) |
| Bibliothèques | streamlit, scikit-learn, numpy, pandas |
| Données | `data/posts.json` — 40 publications **fictives**, 6 thèmes |
| Réseau | Aucun après l'installation |

## 3. Installation

```bash
cd NLP_RECOMM
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt pytest
python -m pytest -q          # doit afficher : 44 passed
streamlit run app.py         # http://localhost:8501
```

## 4. Rappels (5 min)

- **Token** : un mot en minuscules. **Mot vide** : mot fréquent et peu informatif (« le », « pour »).
- **TF-IDF** : `tf × idf`, avec `idf(t) = ln((1+n)/(1+df(t))) + 1`, puis normalisation (longueur 1).
- **Cosinus** entre deux vecteurs de longueur 1 = leur produit scalaire = Σ u[t] × v[t].
- **Profil** = moyenne des vecteurs des posts aimés, renormalisée.

---

## Expérience A — Transformer trois textes en vecteurs (15 min)

Onglet **🧪 Expériences → A**. Textes par défaut :
T1 « Le match de football au stade », T2 « Voyage au stade de Barcelone », T3 « Recette du tajine marocain ».

1. Quels tokens restent pour chaque texte ? Quels mots ont disparu, et pourquoi ?
2. Pourquoi `stade` a-t-il un idf plus faible que `match` ?
3. Vérifiez à la main le poids de `match` dans T1 (indice : calculez d'abord la norme du vecteur brut).
4. Que vaut cos(T1, T2) ? Quel terme en est responsable ?
5. Que vaut cos(T1, T3) ? Les deux textes parlent-ils pourtant d'un sujet sans rapport ?
6. Remplacez T3 par « Tajine à Barcelone après le match ». Prédisez puis observez l'évolution des idf et des cosinus.

## Expérience B — Comparer deux publications (15 min)

Onglet **🧪 → B**. Utilisez les trois boutons de paires.

1. Relevez le cosinus et les termes communs de **p01 / p04** (deux posts football).
2. Même chose pour **p07 / p25** (foot entre amis / tournoi e-sport). Comparez avec la question 1. Surprenant ?
3. Même chose pour **p01 / p07**. Les deux parlent de football : pourquoi le score est-il nul ?
4. Proposez deux modifications du prétraitement qui changeraient le résultat de la question 3.

## Expérience C — Football, puis un intérêt voyage (20 min)

Barre latérale → **⚽ Fan de football** (likes p01, p02, p03).

1. Notez les 8 posts du feed et leurs scores.
2. Dans **🔬 Ouvrir l'algorithme**, choisissez p04 : quels termes expliquent son score ? Vérifiez que la somme des contributions est égale au score.
3. Un post de cuisine apparaît dans le feed. Lequel, et à cause de quel terme ? Comment appelle-t-on ce phénomène ?
4. Cliquez sur **⚽ + ✈️ Football puis voyage** (ajout de p10). Quels posts entrent, sortent, montent ?
5. Pourquoi p09 progresse-t-il plus que les autres posts voyage ?
6. Comparez les deux profils (onglet C). Quel terme passe en tête après l'ajout de p10, et pourquoi un seul like a-t-il autant de poids ?

## Expérience D — Avec et sans exploration (15 min)

Onglet **🧪 → D** (likes p01, p02, p03, p10).

1. À 0 % : quels thèmes sont présents dans le top 8 ? Lesquels sont absents ?
2. À 25 % : combien de places sont réservées ? Quels posts sont choisis ? À quelles positions ?
3. Les scores des posts d'exploration ont-ils été modifiés ? Comment le vérifier ?
4. Passez à 50 %. Décrivez la règle de sélection à partir de ce que vous observez.
5. Avec le scénario **football seul** et 25 %, pourquoi les deux posts d'exploration sont-ils du même thème ?
6. L'exploration fait-elle partie du modèle NLP ? Justifiez.

---

## 5. Questions de synthèse

1. Expliquez la différence entre recommandation **basée sur le contenu**, **filtrage collaboratif** et système **hybride**. Laquelle est implémentée ici ?
2. Qu'est-ce que le **cold start** ? Comment l'application le gère-t-elle ?
3. Citez trois limites du modèle observées pendant le TP, chacune avec un exemple du corpus.
4. Pourquoi l'application affiche-t-elle « score de similarité » et non « probabilité d'aimer » ?
5. Ce simulateur permet-il de conclure à l'existence d'une bulle de filtre ? Quel protocole faudrait-il ?
6. *Bonus code* : dans `recommender/feed.py`, quelle ligne garantit qu'un post aimé n'est jamais proposé ?
