"""Tests de l'interface simple (app.py) : un like déclenche toutes les étapes du moteur."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_cold_start_puis_like():
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    assert any("cold start" in i.value for i in at.info)
    at.button(key="like_p01").click().run()
    assert not at.exception
    assert at.session_state.likes == ["p01"]
    assert any("non aimés" in s.value for s in at.success)


def test_exploration_et_reinitialisation():
    at = AppTest.from_file(APP, default_timeout=60).run()
    for pid in ["p01", "p02"]:
        at.button(key=f"like_{pid}").click().run()
    at.toggle(key="exploration").set_value(True).run()
    assert not at.exception
    assert any("exploration" in s.value for s in at.success)
    at.button[[b.label for b in at.button].index("🔄 Réinitialiser")].click().run()
    assert at.session_state.likes == []
