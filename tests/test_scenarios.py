"""Vérifie que les effets annoncés dans la démo et la documentation sont VRAIS
sur le corpus final. Si les données changent, ces tests échouent."""
import pytest

from recommender import FeedModel, build_feed, load_posts, rank_by_similarity
from recommender.scenarios import SCENARIOS


@pytest.fixture(scope="module")
def m():
    return FeedModel(load_posts())


def ids(r):
    return [i.post_id for i in r.items]


def test_etape2_football(m):
    r = build_feed(m, SCENARIOS["football"]["likes"])
    assert ids(r)[0] == "p04"
    assert "p18" in ids(r)
    contrib = m.term_contributions(m.build_profile(SCENARIOS["football"]["likes"]), "p18")
    assert [c["terme"] for c in contrib] == ["rapide"]


def test_etape3_explication_p04(m):
    contrib = m.term_contributions(m.build_profile(SCENARIOS["football"]["likes"]), "p04")
    assert [c["terme"] for c in contrib] == ["supporters", "match", "stade", "football", "équipe"]


def test_etape4_ajout_voyage(m):
    before = ids(build_feed(m, SCENARIOS["football"]["likes"]))
    after = ids(build_feed(m, SCENARIOS["football_voyage"]["likes"]))
    assert before.index("p09") + 1 == 5 and after.index("p09") + 1 == 2
    assert set(after) - set(before) == {"p15", "p14"}
    assert set(before) - set(after) == {"p05", "p18"}


def test_etape5_exploration(m):
    r = build_feed(m, SCENARIOS["exploration"]["likes"], 0.25)
    assert r.themes_absents == ["cuisine", "fitness"]
    assert [i.post_id for i in r.items if i.origine == "exploration"] == ["p18", "p36"]


def test_experience_b(m):
    assert m.cosine_between("p07", "p25") > m.cosine_between("p01", "p04") > 0
    assert m.cosine_between("p01", "p07") == 0.0


def test_scores_sont_des_similarites_entre_0_et_1(m):
    for _, s in rank_by_similarity(m, SCENARIOS["football_voyage"]["likes"]):
        assert 0.0 <= s <= 1.0 + 1e-12
