# Scénario de démonstration (5 à 7 minutes)

**Avant la présentation** (hors ligne, rien à télécharger) :
```bash
cd NLP_RECOMM && source .venv/bin/activate && streamlit run app.py
```
Ouvrir http://localhost:8501, cliquer sur **🔄 Réinitialiser**, activer **🎤 Mode présentation**
(texte agrandi, parcours guidé en haut de page). Zoom du navigateur conseillé : 110–125 %.

Dans le parcours guidé, **« ▶ Appliquer cette étape »** ou **« Suivant ▶ »** charge l'état exact
de l'étape. En cas de clic malheureux, on retombe toujours sur ses pieds.

| ⏱ | Étape | Action | Ce qu'on voit (vérifié) | Phrase clé |
|---|---|---|---|---|
| 0:00 | **1 · Cold start** | Étape 1 | Feed p01, p09, p17, p08, p22, p29, p02, p10 : un post par thème, badge « non personnalisé », aucun score | « Sans historique, le système ne sait rien : on montre un échantillon équilibré. » |
| 0:45 | **2 · Trois likes football** | Étape 2 (ou ♡ sur p01, p02, p03 via le catalogue) | 1. p04 (0,148) · 2. p06 · 3. p08 (jeu vidéo de foot) · … · 8. p18 **Pâtes** (0,029) | « Le profil est la moyenne des trois vecteurs. Pourquoi des pâtes ? On ouvre l'algorithme. » |
| 1:45 | **3 · Ouvrir l'algorithme** | Onglet 🔬, post p04, puis p18 | p04 : supporters 0,0589 + match 0,0294 + stade 0,0218 + football 0,0197 + équipe 0,0187 = 0,148. p18 : **un seul terme, « rapide »** | « Le score est une somme de produits terme × terme. Le modèle ne comprend pas le sens : “ballon rapide” et “recette rapide”, c'est le même mot. » |
| 3:00 | **4 · Ajout d'un intérêt voyage** | Étape 4 (like p10, road trip au Maroc) | p09 Barcelone **▲3** (5e → 2e) ; **🆕** p15 Jemaa el-Fna et p14 billets d'avion ; p05 et p18 sortent | « Un seul like suffit à déplacer la moyenne. Barcelone combine les deux intérêts : football + voyage. » |
| 4:00 | **5 · Exploration 25 %** | Étape 5 | 2 places sur 8 : p18 (cuisine, 0,026) en position 4 et p36 (fitness, 0,013) en position 8, badge 🧭 | « C'est une règle séparée : on réserve des places à des thèmes absents, sans toucher aux scores. » |
| 5:00 | **6 · Limites** | Onglet 📚 | cos(p01, p07) = 0 (« football » vs « foot ») | « On illustre un mécanisme ; on ne prouve rien sur TikTok ni sur les bulles de filtre. » |
| 6:00 | *(option)* Expérience B | Onglet 🧪 → B, bouton « Foot entre amis vs tournoi e-sport » | cos = 0,271, plus que deux posts football (0,177) | « Le cosinus mesure le vocabulaire partagé, pas le thème. » |

## Plans de secours
- **Le feed ne correspond pas** → **🔄 Réinitialiser**, puis le bouton de scénario dans la barre latérale.
- **L'application ne démarre pas** → vérifier que `.venv` est activé (`which python`), puis relancer.
  `python -m pytest -q` permet de vérifier l'installation en 20 secondes.
- **Pas de vidéoprojecteur adapté** → `python scripts/verifier_resultats.py` dans un terminal affiche
  les mêmes feeds et les mêmes chiffres.

## À ne pas dire
- ❌ « probabilité que l'utilisateur aime » → ✅ « score de similarité »
- ❌ « c'est comme ça que marche TikTok » → ✅ « une famille de méthodes, la recommandation par le contenu »
- ❌ « on voit la bulle de filtre se former » → ✅ « on voit le feed se spécialiser sur un exemple »
