"""Étapes 2 à 4 et 7 — Vecteurs TF-IDF, profil utilisateur, cosinus, explications.

Paramètres TF-IDF réellement utilisés (voir docs/mecanismes.md) :
  tf(t, d)  = nombre d'occurrences de t dans d (pas de log)
  idf(t)    = ln((1 + n) / (1 + df(t))) + 1           (smooth_idf=True)
  vecteur   = tf × idf, puis normalisation L2         (norm="l2")
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .preprocessing import build_document, preprocess


def make_vectorizer() -> TfidfVectorizer:
    """Crée le vectoriseur avec des paramètres explicites (ceux de la doc)."""
    return TfidfVectorizer(
        analyzer=preprocess,  # notre prétraitement remplace celui de sklearn
        use_idf=True,
        smooth_idf=True,
        sublinear_tf=False,
        norm="l2",
    )


@dataclass
class FeedModel:
    """Le corpus vectorisé : une ligne par publication, une colonne par terme."""

    posts: list[dict]

    def __post_init__(self) -> None:
        self.ids = [p["id"] for p in self.posts]
        self.index = {pid: i for i, pid in enumerate(self.ids)}
        self.by_id = {p["id"]: p for p in self.posts}
        self.documents = [build_document(p) for p in self.posts]
        self.vectorizer = make_vectorizer()
        # Matrice creuse (n_posts × n_termes), lignes déjà normalisées (L2)
        self.matrix = self.vectorizer.fit_transform(self.documents)
        self.terms = self.vectorizer.get_feature_names_out()

    # ----- Vecteurs -------------------------------------------------------
    def post_vector(self, post_id: str) -> np.ndarray:
        """Vecteur TF-IDF (dense) d'une publication."""
        return self.matrix[self.index[post_id]].toarray().ravel()

    def post_weights(self, post_id: str) -> list[tuple[str, float]]:
        """Termes non nuls d'une publication, triés par poids décroissant."""
        vec = self.post_vector(post_id)
        nonzero = np.flatnonzero(vec)
        return sorted(
            ((self.terms[j], float(vec[j])) for j in nonzero),
            key=lambda tw: (-tw[1], tw[0]),
        )

    def idf(self, term: str) -> float:
        return float(self.vectorizer.idf_[self.vectorizer.vocabulary_[term]])

    # ----- Profil utilisateur ---------------------------------------------
    def build_profile(self, liked_ids: list[str]) -> np.ndarray | None:
        """Profil = moyenne des vecteurs des posts aimés, puis normalisation L2.

        Retourne None s'il n'y a aucun like (cold start).
        """
        if not liked_ids:
            return None
        rows = [self.index[pid] for pid in liked_ids]
        mean = np.asarray(self.matrix[rows].mean(axis=0)).ravel()
        norm = np.linalg.norm(mean)
        return mean / norm if norm > 0 else None

    def profile_weights(self, profile: np.ndarray, top: int = 10) -> list[tuple[str, float]]:
        order = np.argsort(-profile, kind="stable")[:top]
        return [(self.terms[j], float(profile[j])) for j in order if profile[j] > 0]

    # ----- Similarité -----------------------------------------------------
    def similarity_scores(self, profile: np.ndarray) -> np.ndarray:
        """Similarité cosinus entre le profil et CHAQUE publication."""
        return cosine_similarity(profile.reshape(1, -1), self.matrix).ravel()

    def cosine_between(self, id_a: str, id_b: str) -> float:
        """Similarité cosinus entre deux publications."""
        return float(cosine_similarity(self.matrix[self.index[id_a]],
                                       self.matrix[self.index[id_b]])[0, 0])

    # ----- Explication ----------------------------------------------------
    def term_contributions(self, profile: np.ndarray, post_id: str) -> list[dict]:
        """Décompose le score : cos = Σ profil[t] × post[t] (vecteurs normalisés).

        Chaque terme commun contribue profil[t] × post[t]. La somme de toutes
        les contributions est exactement le score de similarité.
        """
        post = self.post_vector(post_id)
        products = profile * post
        shared = np.flatnonzero(products)
        rows = [
            {
                "terme": self.terms[j],
                "poids_profil": float(profile[j]),
                "poids_post": float(post[j]),
                "contribution": float(products[j]),
            }
            for j in shared
        ]
        return sorted(rows, key=lambda r: (-r["contribution"], r["terme"]))
