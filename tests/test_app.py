"""Tests d'interface sans navigateur (streamlit.testing.AppTest) :
le script app.py est exécuté et on clique sur les vrais boutons."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app_complet.py")


@pytest.fixture
def at():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    return at


def click(at, key):
    at.button(key=key).click().run()
    assert not at.exception


def test_demarrage_sans_like(at):
    assert at.session_state.likes == []
    assert any("cold start" in i.value for i in at.info)


def test_aimer_puis_retirer(at):
    click(at, "feed_p01")
    assert at.session_state.likes == ["p01"]
    assert any("score de similarité" in s.value for s in at.success)
    # p01 est aimé : il n'est plus proposé dans le feed
    assert not any(b.key == "feed_p01" for b in at.button)
    click(at, "side_p01")
    assert at.session_state.likes == []


def test_scenarios_et_reinitialisation(at):
    click(at, "sc_football_voyage")
    assert at.session_state.likes == ["p01", "p02", "p03", "p10"]
    click(at, "sc_exploration")
    assert at.session_state.exploration_pct == 25
    assert any("p18" in s.value and "p36" in s.value for s in at.success)
    at.button[[b.label for b in at.button].index("🔄 Réinitialiser")].click().run()
    assert at.session_state.likes == [] and at.session_state.exploration_pct == 0


def test_catalogue_permet_d_aimer_hors_feed(at):
    click(at, "sc_football")
    click(at, "cat_p10")
    assert at.session_state.likes == ["p01", "p02", "p03", "p10"]


def test_mode_presentation_parcours(at):
    at.toggle[0].set_value(True).run()
    assert not at.exception
    for _ in range(5):
        at.button[[b.label for b in at.button].index("Suivant ▶")].click().run()
        assert not at.exception
    assert at.session_state.tour_step == 5
    assert at.session_state.exploration_pct == 25
