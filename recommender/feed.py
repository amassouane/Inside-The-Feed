"""Étapes 5, 6 et exploration — Construire le feed affiché.

Le modèle NLP (model.py) ne fait que calculer des scores. Ce module décide
QUELLES publications montrer et DANS QUEL ORDRE :
  - sans like : feed initial équilibré, déterministe, non personnalisé ;
  - avec likes : classement par score de similarité décroissant ;
  - exploration : une règle séparée, qui ne modifie aucun score.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .model import FeedModel

FEED_SIZE = 8
# Ordre fixe des thèmes : sert au feed initial et à l'exploration.
CATEGORY_ORDER = ["football", "voyage", "cuisine", "gaming", "technologie", "fitness"]


@dataclass(frozen=True)
class FeedItem:
    post_id: str
    score: float | None   # score de similarité (None pour le feed initial)
    origine: str          # "initial", "pertinence" ou "exploration"


@dataclass
class FeedResult:
    items: list[FeedItem]
    personnalise: bool
    themes_du_top: list[str]          # thèmes du classement de pertinence initial
    themes_absents: list[str]         # thèmes candidats pour l'exploration
    exploration_demandee: int = 0     # nombre de places réservées
    exploration_obtenue: int = 0      # nombre de places réellement remplies


def initial_feed(model: FeedModel, size: int = FEED_SIZE) -> list[FeedItem]:
    """Feed sans like : un post par thème à tour de rôle (plus petit id d'abord).

    Aucun calcul de similarité : ce feed n'est PAS personnalisé.
    """
    queues = {
        cat: sorted(p["id"] for p in model.posts if p["categorie"] == cat)
        for cat in CATEGORY_ORDER
    }
    items: list[FeedItem] = []
    while len(items) < size and any(queues.values()):
        for cat in CATEGORY_ORDER:
            if queues[cat] and len(items) < size:
                items.append(FeedItem(queues[cat].pop(0), None, "initial"))
    return items


def rank_by_similarity(model: FeedModel, liked_ids: list[str]) -> list[tuple[str, float]]:
    """Toutes les publications NON aimées, triées par score décroissant.

    En cas d'égalité, l'identifiant départage (résultat déterministe).
    """
    profile = model.build_profile(liked_ids)
    if profile is None:
        return []
    scores = model.similarity_scores(profile)
    liked = set(liked_ids)
    ranking = [(pid, float(scores[i])) for i, pid in enumerate(model.ids) if pid not in liked]
    return sorted(ranking, key=lambda x: (-x[1], x[0]))


def exploration_slots(size: int, exploration: float) -> int:
    """Nombre de places réservées : arrondi de size × proportion."""
    return int(math.floor(size * exploration + 0.5))


def pick_exploration(model: FeedModel, ranking: list[tuple[str, float]],
                     themes_absents: list[str], k: int) -> list[tuple[str, float]]:
    """Règle d'exploration (indépendante du NLP) :

    on parcourt les thèmes absents dans l'ordre fixe CATEGORY_ORDER et l'on
    prend, à tour de rôle, le meilleur post restant de chaque thème
    (meilleur = premier dans `ranking`, qui exclut déjà les posts aimés).
    """
    queues = {cat: [(pid, s) for pid, s in ranking if model.by_id[pid]["categorie"] == cat]
              for cat in themes_absents}
    picked: list[tuple[str, float]] = []
    while len(picked) < k and any(queues.values()):
        for cat in themes_absents:
            if queues[cat] and len(picked) < k:
                picked.append(queues[cat].pop(0))
    return picked


def build_feed(model: FeedModel, liked_ids: list[str], exploration: float = 0.0,
               size: int = FEED_SIZE) -> FeedResult:
    """Construit le feed affiché (point d'entrée utilisé par l'interface)."""
    if not liked_ids:
        items = initial_feed(model, size)
        themes = sorted({model.by_id[i.post_id]["categorie"] for i in items})
        return FeedResult(items, False, themes, [])

    ranking = rank_by_similarity(model, liked_ids)
    top = ranking[:size]  # classement de pertinence initial (= feed à 0 %)
    themes_top = [c for c in CATEGORY_ORDER if any(model.by_id[p]["categorie"] == c for p, _ in top)]
    themes_absents = [c for c in CATEGORY_ORDER if c not in themes_top]

    k = exploration_slots(size, exploration)
    explore = pick_exploration(model, ranking, themes_absents, k)
    explore_ids = {pid for pid, _ in explore}

    # Les places restantes reçoivent les meilleurs scores (sans doublon).
    relevance = [(p, s) for p, s in ranking if p not in explore_ids][: size - len(explore)]
    items = [FeedItem(p, s, "pertinence") for p, s in relevance]

    # Les posts d'exploration sont insérés à intervalles réguliers.
    if explore:
        step = size // len(explore)
        for n, (pid, s) in enumerate(explore):
            items.insert(min((n + 1) * step - 1, len(items)), FeedItem(pid, s, "exploration"))

    return FeedResult(items, True, themes_top, themes_absents, k, len(explore))
