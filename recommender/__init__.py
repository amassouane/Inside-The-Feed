"""Moteur de recommandation basé sur le contenu (TF-IDF + cosinus).

Aucun import de Streamlit ici : les calculs sont testables seuls.
"""
from .feed import FEED_SIZE, CATEGORY_ORDER, build_feed, initial_feed, rank_by_similarity
from .model import FeedModel, make_vectorizer
from .preprocessing import build_document, load_posts, preprocess, remove_stopwords, tokenize

__all__ = [
    "FEED_SIZE", "CATEGORY_ORDER", "build_feed", "initial_feed", "rank_by_similarity",
    "FeedModel", "make_vectorizer",
    "build_document", "load_posts", "preprocess", "remove_stopwords", "tokenize",
]
