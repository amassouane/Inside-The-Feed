"""Étape 1 — Prétraitement du texte : minuscules, tokenisation, mots vides.

Ce module ne dépend ni de scikit-learn ni de Streamlit : il transforme
simplement une publication en liste de mots (tokens) utiles.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Un token = une suite de lettres (accents compris). Les chiffres, la
# ponctuation, les apostrophes et le « # » servent de séparateurs.
TOKEN_PATTERN = re.compile(r"[a-zàâäçéèêëîïôöùûüÿœæ]+")
MIN_TOKEN_LENGTH = 2


def load_posts(path: Path | None = None) -> list[dict]:
    """Charge les publications fictives depuis data/posts.json."""
    path = path or DATA_DIR / "posts.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["posts"]


@lru_cache(maxsize=1)
def load_stopwords(path: Path | None = None) -> frozenset[str]:
    """Charge la liste locale de mots vides (un mot par ligne, # = commentaire)."""
    path = path or DATA_DIR / "stopwords_fr.txt"
    with open(path, encoding="utf-8") as f:
        return frozenset(
            line.strip().lower()
            for line in f
            if line.strip() and not line.startswith("#")
        )


def build_document(post: dict) -> str:
    """Concatène titre + description + hashtags : c'est le texte analysé.

    La catégorie n'est PAS incluse : elle ne sert qu'à l'affichage.
    """
    return " ".join([post["titre"], post["description"], " ".join(post["hashtags"])])


def tokenize(text: str) -> list[str]:
    """Met en minuscules et découpe le texte en mots (tokens bruts)."""
    return [
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if len(token) >= MIN_TOKEN_LENGTH
    ]


def remove_stopwords(tokens: list[str]) -> list[str]:
    """Retire les mots vides (« le », « de », « pour »...)."""
    stopwords = load_stopwords()
    return [token for token in tokens if token not in stopwords]


def preprocess(text: str) -> list[str]:
    """Chaîne complète : texte brut → tokens utiles.

    C'est cette fonction que TfidfVectorizer utilise comme `analyzer`.
    """
    return remove_stopwords(tokenize(text))
