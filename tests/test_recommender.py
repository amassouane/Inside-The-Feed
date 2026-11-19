"""Tests des calculs (sans Streamlit). Lancement : python -m pytest -q"""
import math

import numpy as np
import pytest

from recommender import (CATEGORY_ORDER, build_document, FEED_SIZE, FeedModel, build_feed, load_posts,
                         make_vectorizer, preprocess, rank_by_similarity, tokenize)
from recommender.feed import exploration_slots


@pytest.fixture(scope="module")
def m():
    return FeedModel(load_posts())


# --- Données ---------------------------------------------------------------
def test_corpus_fictif_complet(m):
    assert len(m.posts) == 40
    assert len(set(m.ids)) == 40
    assert {p["categorie"] for p in m.posts} == set(CATEGORY_ORDER)
    for p in m.posts:
        assert {"id", "titre", "description", "hashtags", "categorie"} <= p.keys()


# --- Prétraitement ---------------------------------------------------------
def test_preprocess_minuscules_stopwords_hashtags():
    assert tokenize("Le MATCH de l'équipe #Football") == ["le", "match", "de", "équipe", "football"]
    assert preprocess("Le MATCH de l'équipe #Football") == ["match", "équipe", "football"]


def test_categorie_absente_du_texte_analyse():
    post = {"titre": "Titre", "description": "Texte.", "hashtags": ["#tag"], "categorie": "zzzcat"}
    assert "zzzcat" not in build_document(post)


# --- TF-IDF ----------------------------------------------------------------
def test_lignes_normalisees(m):
    norms = np.sqrt(m.matrix.multiply(m.matrix).sum(axis=1)).A.ravel()
    assert np.allclose(norms, 1.0)


def test_formule_idf_documentee(m):
    n = len(m.posts)
    df = (m.matrix > 0).sum(axis=0).A.ravel()
    assert np.allclose(m.vectorizer.idf_, np.log((1 + n) / (1 + df)) + 1)


def test_exemple_numerique_de_la_doc():
    vec = make_vectorizer()
    X = vec.fit_transform(["Le match de football au stade", "Voyage au stade de Barcelone",
                           "Recette du tajine marocain"]).toarray()
    terms = list(vec.get_feature_names_out())
    assert math.isclose(vec.idf_[terms.index("stade")], math.log(4 / 3) + 1, rel_tol=1e-9)
    assert math.isclose(X[0][terms.index("match")], 0.6228, abs_tol=1e-4)
    assert math.isclose(X[0][terms.index("stade")], 0.4736, abs_tol=1e-4)
    assert math.isclose(float(X[0] @ X[1]), 0.2243, abs_tol=1e-4)
    assert float(X[0] @ X[2]) == 0.0


# --- Profil et scores --------------------------------------------------------
def test_profil_vide(m):
    assert m.build_profile([]) is None
    assert rank_by_similarity(m, []) == []


def test_profil_normalise_et_moyenne(m):
    likes = ["p01", "p02", "p03"]
    prof = m.build_profile(likes)
    assert math.isclose(np.linalg.norm(prof), 1.0)
    mean = sum(m.post_vector(p) for p in likes) / 3
    assert np.allclose(prof, mean / np.linalg.norm(mean))


def test_cosinus_egal_produit_scalaire(m):
    prof = m.build_profile(["p01", "p10"])
    dense = m.matrix.toarray()
    assert np.allclose(m.similarity_scores(prof), dense @ prof)


def test_contributions_somment_au_score(m):
    prof = m.build_profile(["p01", "p02", "p03"])
    scores = m.similarity_scores(prof)
    for pid in m.ids:
        total = sum(c["contribution"] for c in m.term_contributions(prof, pid))
        assert math.isclose(total, scores[m.index[pid]], abs_tol=1e-12)


# --- Feed --------------------------------------------------------------------
def test_feed_initial_equilibre_deterministe(m):
    r1, r2 = build_feed(m, []), build_feed(m, [])
    assert [i.post_id for i in r1.items] == [i.post_id for i in r2.items]
    assert not r1.personnalise
    assert all(i.score is None and i.origine == "initial" for i in r1.items)
    first = [m.by_id[i.post_id]["categorie"] for i in r1.items[:len(CATEGORY_ORDER)]]
    assert first == CATEGORY_ORDER


def test_remise_a_zero_redonne_le_feed_initial(m):
    initial = [i.post_id for i in build_feed(m, []).items]
    build_feed(m, ["p01", "p02"], 0.3)  # aucun état caché
    assert [i.post_id for i in build_feed(m, []).items] == initial


@pytest.mark.parametrize("likes", [["p01"], ["p01", "p02", "p03"], ["p01", "p02", "p03", "p10"],
                                   ["p17", "p24", "p33"]])
@pytest.mark.parametrize("expl", [0, 0.1, 0.25, 0.5])
def test_feed_sans_doublon_ni_post_aime(m, likes, expl):
    r = build_feed(m, likes, expl)
    ids = [i.post_id for i in r.items]
    assert len(ids) == FEED_SIZE
    assert len(set(ids)) == len(ids)
    assert not set(ids) & set(likes)


def test_classement_decroissant(m):
    r = build_feed(m, ["p01", "p02", "p03"])
    scores = [i.score for i in r.items]
    assert scores == sorted(scores, reverse=True)


# --- Exploration -------------------------------------------------------------
def test_exploration_zero_egale_classement_pur(m):
    likes = ["p01", "p02", "p03", "p10"]
    pure = [p for p, _ in rank_by_similarity(m, likes)[:FEED_SIZE]]
    assert [i.post_id for i in build_feed(m, likes, 0).items] == pure


def test_exploration_themes_absents_et_scores_inchanges(m):
    likes = ["p01", "p02", "p03", "p10"]
    scores = dict(rank_by_similarity(m, likes))
    r = build_feed(m, likes, 0.25)
    explore = [i for i in r.items if i.origine == "exploration"]
    assert r.exploration_demandee == exploration_slots(FEED_SIZE, 0.25) == 2
    assert len(explore) == 2
    for it in explore:
        assert m.by_id[it.post_id]["categorie"] in r.themes_absents
        assert it.score == scores[it.post_id]
    for it in r.items:
        assert it.score == scores[it.post_id]


def test_exploration_sans_theme_absent_ne_force_rien(m):
    # Si le top couvre déjà tous les thèmes absents possibles, aucune place n'est remplie.
    likes = ["p01", "p02", "p03", "p10"]
    r = build_feed(m, likes, 0.25)
    from recommender.feed import pick_exploration
    assert pick_exploration(m, rank_by_similarity(m, likes), [], 3) == []
    assert r.exploration_obtenue <= r.exploration_demandee


def test_exploration_deterministe(m):
    a = build_feed(m, ["p01", "p02", "p03"], 0.5)
    b = build_feed(m, ["p01", "p02", "p03"], 0.5)
    assert a.items == b.items
