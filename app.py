"""Inside the Feed — version simple.

À gauche : un feed comme dans une vraie application. À droite : à chaque like,
toutes les étapes du moteur s'affichent, de la plus simple à la plus complète.
L'ancienne interface complète (onglets, expériences, mode présentation) est dans app_complet.py.

Lancement :  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from recommender import FEED_SIZE, FeedModel, build_document, build_feed, load_posts, preprocess, tokenize
from recommender.preprocessing import load_stopwords
from ui_style import card_html, chip, css, fr

st.set_page_config(page_title="Inside the Feed", page_icon="📡", layout="wide")


@st.cache_resource
def get_model() -> FeedModel:
    return FeedModel(load_posts())


m = get_model()
st.session_state.setdefault("likes", [])
st.session_state.setdefault("prev_feed", None)
st.session_state.setdefault("exploration", False)


def feed_ids() -> list[str]:
    return [it.post_id for it in current_feed().items]


def current_feed():
    return build_feed(m, st.session_state.likes, 0.25 if st.session_state.exploration else 0.0)


def like(pid: str) -> None:
    st.session_state.prev_feed = feed_ids()
    st.session_state.likes = st.session_state.likes + [pid]


def reset() -> None:
    st.session_state.likes = []
    st.session_state.prev_feed = None


def src(path: str) -> None:
    st.caption(f"📄 `{path}`")


st.markdown(css(False), unsafe_allow_html=True)
st.markdown("<style>.block-container{max-width:1500px}</style>", unsafe_allow_html=True)

top1, top2, top3 = st.columns([5, 2, 1.2])
top1.markdown("## 📡 Inside the Feed")
top2.toggle("🧭 Exploration 25 %", key="exploration", on_change=lambda: st.session_state.update(prev_feed=feed_ids()))
top3.button("🔄 Réinitialiser", on_click=reset, width="stretch")

likes = st.session_state.likes
feed = current_feed()
left, right = st.columns([1, 1.25], gap="large")

# --------------------------------------------------------------------------
# Gauche : le feed
# --------------------------------------------------------------------------
with left:
    st.markdown(f"**❤️ Mes likes :** {', '.join(likes) if likes else 'aucun'}")
    prev = st.session_state.prev_feed
    for rank, item in enumerate(feed.items, 1):
        post = m.by_id[item.post_id]
        move = ""
        if prev is not None and likes:
            move = "🆕 nouveau" if item.post_id not in prev else (
                f"▲ {prev.index(item.post_id) + 1 - rank}" if prev.index(item.post_id) + 1 > rank else "")
        with st.container(border=True):
            st.markdown(card_html(post, rank, item.score, item.origine, move), unsafe_allow_html=True)
            st.button("♡ J'aime", key=f"like_{item.post_id}", on_click=like, args=(item.post_id,))

# --------------------------------------------------------------------------
# Droite : ce que le moteur vient de calculer
# --------------------------------------------------------------------------
with right:
    st.markdown("### ⚙️ Ce que le moteur vient de faire")
    if not likes:
        st.info("**Aucun like → aucun profil → aucun score.** C'est le *cold start* : le feed montre "
                "un post par thème, à tour de rôle (football, voyage, cuisine, gaming, technologie, fitness). "
                "Cliquez sur ♡ J'aime pour lancer le moteur.")
        src("recommender/feed.py → initial_feed()")
        st.stop()

    last = likes[-1]
    post = m.by_id[last]
    profile = m.build_profile(likes)

    st.markdown(f"#### 1 · Texte du post aimé ({last})")
    doc = build_document(post)
    st.write(doc)
    st.caption("titre + description + hashtags (la catégorie n'est pas lue)")
    src("recommender/preprocessing.py → build_document()")

    st.markdown("#### 2 · Tokens")
    raw, stop = tokenize(doc), load_stopwords()
    st.markdown("".join(chip(t, "stop" if t in stop else "token") for t in raw), unsafe_allow_html=True)
    st.caption(f"minuscules, découpage en mots, mots vides barrés : {len(raw)} tokens → {len(preprocess(doc))} gardés")
    src("recommender/preprocessing.py → preprocess()")

    st.markdown("#### 3 · Vecteur TF-IDF du post")
    st.dataframe([{"mot": t, "poids": round(w, 3)} for t, w in m.post_weights(last)[:6]],
                 hide_index=True, width="stretch")
    st.caption(f"poids = tf × idf, puis longueur 1 · un vecteur de {len(m.terms)} nombres, presque tous nuls")
    src("recommender/model.py → make_vectorizer()")

    st.markdown(f"#### 4 · Profil = moyenne de vos {len(likes)} like(s)")
    st.dataframe([{"mot": t, "poids": round(w, 3)} for t, w in m.profile_weights(profile, 6)],
                 hide_index=True, width="stretch")
    st.caption("moyenne des vecteurs aimés, puis longueur 1 : vous devenez un vecteur")
    src("recommender/model.py → build_profile()")

    st.markdown("#### 5 · Score de chaque post = cosinus(profil, post)")
    best = next(it for it in feed.items if it.origine != "exploration")
    contrib = m.term_contributions(profile, best.post_id)
    st.markdown(f"Pourquoi **{best.post_id}** est n°1 (score **{fr(best.score)}**) :")
    st.dataframe([{"mot commun": c["terme"], "profil × post": f"{fr(c['poids_profil'])} × {fr(c['poids_post'])}",
                   "= contribution": round(c["contribution"], 4)} for c in contrib],
                 hide_index=True, width="stretch")
    st.caption("score = somme des contributions des mots communs (similarité, pas probabilité)")
    src("recommender/model.py → similarity_scores(), term_contributions()")

    st.markdown("#### 6 · Nouveau feed")
    lines = [f"posts non aimés triés par score : les {FEED_SIZE} premiers sont affichés"]
    if feed.exploration_obtenue:
        explo = [it.post_id for it in feed.items if it.origine == "exploration"]
        lines.append(f"exploration : {feed.exploration_obtenue} place(s) pour les thèmes absents "
                     f"({', '.join(feed.themes_absents)}) → {', '.join(explo)} · scores inchangés")
    if prev:
        new = [p for p in feed_ids() if p not in prev]
        gone = [p for p in prev if p not in feed_ids() and p != last]
        if new or gone:
            lines.append(f"entrent : {', '.join(new) or '—'} · sortent : {', '.join(gone) or '—'}")
    st.success("  \n".join(lines))
    src("recommender/feed.py → rank_by_similarity(), build_feed()")
