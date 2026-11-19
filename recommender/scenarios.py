"""Scénarios prédéfinis, expériences A–D et parcours guidé.

Tout est figé ici pour que la démonstration soit reproductible. Les effets
annoncés dans les textes sont vérifiés par tests/test_scenarios.py.
"""

FOOTBALL_LIKES = ["p01", "p02", "p03"]
VOYAGE_LIKE = "p10"

SCENARIOS = {
    "vide": {
        "label": "🧊 Aucun like",
        "aide": "Cold start : le feed initial n'est pas personnalisé.",
        "likes": [],
        "exploration": 0,
    },
    "football": {
        "label": "⚽ Fan de football",
        "aide": "Aime p01, p02 et p03 (trois posts football).",
        "likes": FOOTBALL_LIKES,
        "exploration": 0,
    },
    "football_voyage": {
        "label": "⚽ + ✈️ Football puis voyage",
        "aide": "Ajoute p10 (road trip au Maroc) aux trois likes football.",
        "likes": FOOTBALL_LIKES + [VOYAGE_LIKE],
        "exploration": 0,
    },
    "exploration": {
        "label": "🧭 Football + voyage, exploration 25 %",
        "aide": "Mêmes likes, 2 places sur 8 réservées à des thèmes absents.",
        "likes": FOOTBALL_LIKES + [VOYAGE_LIKE],
        "exploration": 25,
    },
}

# Expérience A : trois textes courts, vectorisés SEULS (corpus de 3 documents).
EXPERIENCE_A_TEXTS = [
    "Le match de football au stade",
    "Voyage au stade de Barcelone",
    "Recette du tajine marocain",
]

# Expérience B : paires à comparer avec le cosinus.
EXPERIENCE_B_PAIRS = [
    ("p01", "p04", "Deux posts football"),
    ("p07", "p25", "Foot entre amis vs tournoi e-sport"),
    ("p01", "p07", "« football » vs « foot »"),
]

EXPERIENCE_D_EXPLORATION = 25

# Parcours guidé du mode présentation.
TOUR = [
    {
        "titre": "1 · Le feed sans historique",
        "scenario": "vide",
        "onglet": "📱 Feed",
        "dire": "Aucun like : le système ne sait rien de nous. C'est le « cold start ».",
        "observer": "Un post par thème, à tour de rôle. Aucun score : ce feed n'est pas personnalisé.",
    },
    {
        "titre": "2 · Trois likes football",
        "scenario": "football",
        "onglet": "📱 Feed",
        "dire": "On aime trois posts football. Le profil devient la moyenne de leurs vecteurs TF-IDF.",
        "observer": "p04 (Coupe d'Afrique) passe en tête. Les pâtes (p18) apparaissent à cause du seul mot « rapide ».",
    },
    {
        "titre": "3 · Ouvrir l'algorithme",
        "scenario": "football",
        "onglet": "🔬 Ouvrir l'algorithme",
        "dire": "Pourquoi p04 ? Le score est une somme : profil[t] × post[t] pour chaque terme commun.",
        "observer": "« supporters », « match », « stade », « football », « équipe » expliquent tout le score.",
    },
    {
        "titre": "4 · Un nouvel intérêt : voyage",
        "scenario": "football_voyage",
        "onglet": "📱 Feed",
        "dire": "On ajoute un like voyage (p10). Le profil se déplace vers le vocabulaire du voyage.",
        "observer": "p09 (Barcelone : football + voyage) monte de la 5e à la 2e place ; p15 et p14 entrent ; p05 et p18 sortent.",
    },
    {
        "titre": "5 · Exploration 25 %",
        "scenario": "exploration",
        "onglet": "📱 Feed",
        "dire": "Une règle séparée réserve 2 places sur 8 à des thèmes absents du top (cuisine, fitness).",
        "observer": "p18 et p36 sont marqués « exploration » ; leurs scores ne sont pas modifiés.",
    },
    {
        "titre": "6 · Ce que la démo ne prouve pas",
        "scenario": "exploration",
        "onglet": "📚 Comprendre & limites",
        "dire": "40 posts fictifs, un utilisateur, aucune donnée réelle : on illustre un mécanisme.",
        "observer": "Pas de conclusion sur TikTok/Instagram, ni sur les bulles de filtre.",
    },
]
