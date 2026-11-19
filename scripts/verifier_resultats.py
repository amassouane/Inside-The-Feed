"""Affiche tous les chiffres cités dans la démo et la documentation, calculés sur le
corpus final. Lancement : python scripts/verifier_resultats.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.metrics.pairwise import cosine_similarity  # noqa: E402

from recommender import (FeedModel, build_feed, load_posts, make_vectorizer,  # noqa: E402
                         preprocess, rank_by_similarity)
from recommender.scenarios import EXPERIENCE_A_TEXTS, EXPERIENCE_B_PAIRS, SCENARIOS  # noqa: E402

m = FeedModel(load_posts())


def titre(t):
    print(f"\n{'=' * 70}\n{t}\n{'=' * 70}")


def feed_table(likes, expl=0.0):
    r = build_feed(m, likes, expl)
    for i, it in enumerate(r.items, 1):
        p = m.by_id[it.post_id]
        s = "   —  " if it.score is None else f"{it.score:.4f}"
        print(f"  {i}. {it.post_id}  {s}  {it.origine:<11} {p['categorie']:<11} {p['titre']}")
    return r


titre("Corpus")
print(f"{len(m.posts)} posts, vocabulaire de {len(m.terms)} termes, "
      f"{m.matrix.nnz} valeurs non nulles ({100 * m.matrix.nnz / (m.matrix.shape[0] * m.matrix.shape[1]):.1f} %)")

titre("Expérience A — trois textes seuls")
vec = make_vectorizer()
X = vec.fit_transform(EXPERIENCE_A_TEXTS)
for t in EXPERIENCE_A_TEXTS:
    print(f"  {t!r} -> {preprocess(t)}")
for term, idf in zip(vec.get_feature_names_out(), vec.idf_):
    print(f"  idf({term}) = {idf:.4f}")
for i, row in enumerate(X.toarray()):
    print(f"  Texte {i + 1}: " + ", ".join(f"{t}={w:.4f}" for t, w in zip(vec.get_feature_names_out(), row) if w))
print("  cosinus :\n", cosine_similarity(X).round(4))

titre("Expérience B — paires")
for a, b, label in EXPERIENCE_B_PAIRS:
    shared = m.term_contributions(m.post_vector(a), b)
    print(f"  {label}: cos({a},{b}) = {m.cosine_between(a, b):.4f}  termes communs: "
          + ", ".join(f"{c['terme']} ({c['contribution']:.4f})" for c in shared))

titre("Feed initial (aucun like)")
feed_table([])

for key in ["football", "football_voyage"]:
    likes = SCENARIOS[key]["likes"]
    titre(f"Expérience C — likes {likes}")
    feed_table(likes)
    prof = m.build_profile(likes)
    print("  Profil (10 termes) : " + ", ".join(f"{t}={w:.3f}" for t, w in m.profile_weights(prof, 10)))
    for pid in ["p04", "p09", "p18"]:
        cs = m.term_contributions(prof, pid)
        print(f"  {pid}: " + ", ".join(f"{c['terme']} {c['poids_profil']:.3f}×{c['poids_post']:.3f}="
                                      f"{c['contribution']:.4f}" for c in cs))
    print("  Rangs 9-12 :", [(p, round(s, 4)) for p, s in rank_by_similarity(m, likes)[8:12]])

titre("Expérience D — exploration")
likes = SCENARIOS["exploration"]["likes"]
for pct in [0, 25, 50]:
    print(f"\n  Exploration {pct} %")
    r = feed_table(likes, pct / 100)
    print(f"  thèmes du top: {r.themes_du_top} / absents: {r.themes_absents} / "
          f"places {r.exploration_obtenue}/{r.exploration_demandee}")
print("\n  Football seul, exploration 25 %")
r = feed_table(SCENARIOS["football"]["likes"], 0.25)
print(f"  absents: {r.themes_absents}")
