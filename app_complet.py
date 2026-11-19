"""Inside the Feed — interface Streamlit.

Lancement :  streamlit run app.py
Ce fichier ne fait QUE de l'affichage : tous les calculs sont dans recommender/.
"""
from __future__ import annotations

import inspect
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity

from recommender import (FEED_SIZE, FeedModel, build_document, build_feed, load_posts,
                         make_vectorizer, preprocess, rank_by_similarity, tokenize)
from recommender import feed as feed_module
from recommender import model as model_module
from recommender import preprocessing as prep_module
from recommender.preprocessing import load_stopwords
from recommender.scenarios import (EXPERIENCE_A_TEXTS, EXPERIENCE_B_PAIRS,
                                   EXPERIENCE_D_EXPLORATION, SCENARIOS, TOUR)
from ui_style import CATEGORY_STYLE, card_html, chip, css, fr

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Inside the Feed", page_icon="📡", layout="wide")


@st.cache_resource
def get_model() -> FeedModel:
    return FeedModel(load_posts())


m = get_model()

# --------------------------------------------------------------------------
# État de session et actions
# --------------------------------------------------------------------------
st.session_state.setdefault("likes", [])
st.session_state.setdefault("exploration_pct", 0)
st.session_state.setdefault("prev_feed", None)
st.session_state.setdefault("tour_step", 0)
st.session_state.setdefault("presentation", False)


def current_feed():
    return build_feed(m, st.session_state.likes, st.session_state.exploration_pct / 100)


def _snapshot() -> None:
    """Mémorise le feed avant une action, pour afficher les mouvements."""
    st.session_state.prev_feed = [it.post_id for it in current_feed().items]


def toggle_like(pid: str) -> None:
    _snapshot()
    likes = st.session_state.likes
    st.session_state.likes = [x for x in likes if x != pid] if pid in likes else likes + [pid]


def apply_scenario(key: str) -> None:
    _snapshot()
    sc = SCENARIOS[key]
    st.session_state.likes = list(sc["likes"])
    st.session_state.exploration_pct = sc["exploration"]


def reset() -> None:
    st.session_state.likes = []
    st.session_state.exploration_pct = 0
    st.session_state.prev_feed = None


def go_step(i: int) -> None:
    st.session_state.tour_step = i
    apply_scenario(TOUR[i]["scenario"])


def show_code(fn, label: str | None = None) -> None:
    """Affiche le code source RÉEL d'une fonction du projet."""
    path = Path(inspect.getsourcefile(fn)).resolve().relative_to(ROOT)
    with st.expander(f"💻 Voir le code : `{fn.__name__}` — {label or path}"):
        st.code(inspect.getsource(fn), language="python")


def post_label(pid: str) -> str:
    p = m.by_id[pid]
    return f"{CATEGORY_STYLE[p['categorie']]['emoji']} {pid} — {p['titre']}"


def styled_matrix(df: pd.DataFrame):
    vmax = float(df.values.max()) or 1.0
    return df.style.format("{:.3f}").map(
        lambda v: f"background-color: rgba(99,102,241,{0.85 * v / vmax:.2f});"
                  + ("color:white;" if v / vmax > 0.55 else ""))


# --------------------------------------------------------------------------
# Barre latérale
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📡 Inside the Feed")
    st.caption("Démonstrateur interactif —**données 100 % fictives**.")
    st.toggle("🎤 Mode présentation", key="presentation")

    st.markdown("### 🎬 Scénarios")
    for key, sc in SCENARIOS.items():
        st.button(sc["label"], key=f"sc_{key}", help=sc["aide"], on_click=apply_scenario,
                  args=(key,), width="stretch")

    st.markdown("### 🧭 Exploration")
    st.slider("Part du feed réservée à l'exploration (%)", 0, 50, step=5, key="exploration_pct",
              on_change=_snapshot)
    k = feed_module.exploration_slots(FEED_SIZE, st.session_state.exploration_pct / 100)
    st.caption(f"→ {k} place(s) sur {FEED_SIZE}. Règle séparée du modèle NLP.")

    st.markdown(f"### ❤️ Mes likes ({len(st.session_state.likes)})")
    if not st.session_state.likes:
        st.caption("Aucun like pour l'instant.")
    for pid in st.session_state.likes:
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"<small>{post_label(pid)}</small>", unsafe_allow_html=True)
        c2.button("✕", key=f"side_{pid}", on_click=toggle_like, args=(pid,), help="Retirer le like")

    st.button("🔄 Réinitialiser", on_click=reset, type="primary", width="stretch")

st.markdown(css(st.session_state.presentation), unsafe_allow_html=True)

st.markdown("""
<div class="hero"><h1>📡 Inside the Feed</h1>
<p>Comment un moteur de recommandation transforme des textes et des likes en feed personnalisé —
TF-IDF · profil utilisateur · similarité cosinus</p></div>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------
# Parcours guidé (mode présentation)
# --------------------------------------------------------------------------
if st.session_state.presentation:
    i = st.session_state.tour_step
    step = TOUR[i]
    st.markdown(f"""<div class="tour"><h3>🎤 {step['titre']}</h3>
<b>À dire :</b> {step['dire']}<br><b>À observer :</b> {step['observer']}<br>
<small>👉 Onglet : <b>{step['onglet']}</b> · étape {i + 1}/{len(TOUR)}</small></div>""",
                unsafe_allow_html=True)
    c1, c2, c3, _ = st.columns([1.4, 2.2, 1.4, 2.5])
    c1.button("◀ Précédent", disabled=i == 0, on_click=go_step, args=(max(i - 1, 0),))
    c2.button("▶ Appliquer cette étape", type="primary", on_click=go_step, args=(i,))
    c3.button("Suivant ▶", disabled=i == len(TOUR) - 1, on_click=go_step,
              args=(min(i + 1, len(TOUR) - 1),))

feed = current_feed()
likes = st.session_state.likes
profile = m.build_profile(likes)

tab_feed, tab_algo, tab_exp, tab_learn = st.tabs(
    ["📱 Feed", "🔬 Ouvrir l'algorithme", "🧪 Expériences", "📚 Comprendre & limites"])

# --------------------------------------------------------------------------
# Onglet 1 — Feed
# --------------------------------------------------------------------------
with tab_feed:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Likes", len(likes))
    c2.metric("Personnalisé ?", "Oui" if feed.personnalise else "Non")
    c3.metric("Exploration", f"{feed.exploration_obtenue}/{FEED_SIZE} places")
    c4.metric("Vocabulaire", f"{len(m.terms)} termes", help=f"{len(m.posts)} posts fictifs")

    if not feed.personnalise:
        st.info("**Feed initial (cold start)** : aucun like, donc aucun profil. On affiche un post "
                "par thème à tour de rôle (ordre fixe, plus petit identifiant d'abord). "
                "Ce classement n'est **pas personnalisé**. Aimez un post pour lancer le calcul.")
    else:
        msg = (f"Classé par **score de similarité** (cosinus) entre votre profil et chaque post "
               f"non aimé. Thèmes du top {FEED_SIZE} : {', '.join(feed.themes_du_top)}.")
        if feed.exploration_demandee:
            explored = [it.post_id for it in feed.items if it.origine == "exploration"]
            msg += (f"\n\n🧭 **Exploration** : {feed.exploration_obtenue}/{feed.exploration_demandee} "
                    f"place(s) remplie(s) avec des thèmes absents ({', '.join(feed.themes_absents) or 'aucun'}) "
                    f"→ {', '.join(explored) or 'aucun post disponible'}.")
        st.success(msg)

    prev = st.session_state.prev_feed
    cols = st.columns(2)
    for rank, item in enumerate(feed.items, start=1):
        post = m.by_id[item.post_id]
        move = ""
        if prev is not None:
            if item.post_id not in prev:
                move = "🆕 nouveau"
            elif (d := prev.index(item.post_id) + 1 - rank) != 0:
                move = f"▲ {d}" if d > 0 else f"▼ {-d}"
        with cols[(rank - 1) % 2].container(border=True):
            st.markdown(card_html(post, rank, item.score, item.origine, move), unsafe_allow_html=True)
            st.button("♡ Aimer", key=f"feed_{item.post_id}", on_click=toggle_like,
                      args=(item.post_id,), width="stretch")
            if profile is not None:
                with st.expander("Pourquoi ce post ?"):
                    contribs = m.term_contributions(profile, item.post_id)
                    if item.origine == "exploration":
                        st.caption("Choisi par la règle d'exploration (thème absent du top), "
                                   "pas pour son score. Score affiché = score réel, non modifié.")
                    if contribs:
                        st.markdown("Termes communs avec votre profil (profil × post) :")
                        for c in contribs[:4]:
                            st.markdown(f"- **{c['terme']}** : {fr(c['poids_profil'])} × "
                                        f"{fr(c['poids_post'])} = **{fr(c['contribution'], 4)}**")
                        if len(contribs) > 4:
                            st.caption(f"+ {len(contribs) - 4} autre(s) terme(s).")
                    else:
                        st.caption("Aucun terme commun : score = 0.")

    with st.expander(f"📚 Catalogue complet — {len(m.posts)} publications fictives "
                     "(pour aimer un post absent du feed)"):
        cat = st.pills("Filtrer par thème (affichage seulement)", list(CATEGORY_STYLE),
                       format_func=lambda c: f"{CATEGORY_STYLE[c]['emoji']} {CATEGORY_STYLE[c]['label']}",
                       key="catalog_filter")
        for p in m.posts:
            if cat and p["categorie"] != cat:
                continue
            c1, c2 = st.columns([6, 1.3])
            c1.markdown(post_label(p["id"]))
            liked = p["id"] in likes
            c2.button("💔 Retirer" if liked else "♡ Aimer", key=f"cat_{p['id']}",
                      on_click=toggle_like, args=(p["id"],), width="stretch")

# --------------------------------------------------------------------------
# Onglet 2 — Ouvrir l'algorithme
# --------------------------------------------------------------------------
with tab_algo:
    st.markdown("Suivez **un exemple concret** : texte original → tokens → poids TF-IDF → profil → "
                "scores → classement. Chaque étape renvoie à la fonction réelle du code.")
    default = feed.items[0].post_id
    pid = st.selectbox("Publication à suivre", m.ids, index=m.ids.index(default),
                       format_func=post_label, key="trace_post")

    # 1. Texte original
    st.markdown('<div class="step"><b>① Texte original</b> — titre + description + hashtags '
                '(la catégorie n\'est pas utilisée dans le calcul)</div>', unsafe_allow_html=True)
    doc = build_document(m.by_id[pid])
    st.code(doc, language=None, wrap_lines=True)
    show_code(build_document)

    # 2. Tokens
    st.markdown('<div class="step"><b>② Tokens</b> — minuscules, découpage en mots, '
                'suppression des mots vides (barrés)</div>', unsafe_allow_html=True)
    stop = load_stopwords()
    raw = tokenize(doc)
    st.markdown("".join(chip(t, "stop" if t in stop else "token") for t in raw), unsafe_allow_html=True)
    kept = preprocess(doc)
    st.caption(f"{len(raw)} tokens bruts → {len(kept)} tokens conservés "
               f"({len(raw) - len(kept)} mots vides retirés).")
    show_code(tokenize)
    show_code(preprocess)

    # 3. Poids TF-IDF
    st.markdown('<div class="step"><b>③ Poids TF-IDF</b> — tf × idf, puis normalisation L2 '
                '(longueur du vecteur = 1)</div>', unsafe_allow_html=True)
    tf = Counter(kept)
    rows = [{"terme": t, "tf": n, "idf": m.idf(t), "tf × idf": n * m.idf(t)} for t, n in tf.items()]
    df_w = pd.DataFrame(rows)
    df_w["poids normalisé"] = df_w["tf × idf"] / np.sqrt((df_w["tf × idf"] ** 2).sum())
    df_w = df_w.sort_values(["poids normalisé", "terme"], ascending=[False, True])
    st.dataframe(df_w, hide_index=True, width="stretch", height=260,
                 column_config={c: st.column_config.NumberColumn(format="%.3f")
                                for c in ["idf", "tf × idf", "poids normalisé"]})
    check = max(abs(w - dict(m.post_weights(pid))[t]) for t, w in zip(df_w["terme"], df_w["poids normalisé"]))
    st.caption(f"✅ Recalcul manuel = valeurs de scikit-learn (écart max {check:.1e}). "
               f"idf(t) = ln((1+n)/(1+df(t))) + 1 avec n = {len(m.posts)}.")
    show_code(model_module.make_vectorizer)

    # 4. Profil
    st.markdown('<div class="step"><b>④ Profil utilisateur</b> — moyenne des vecteurs des posts '
                'aimés, puis normalisation L2</div>', unsafe_allow_html=True)
    if profile is None:
        st.warning("Aucun like : pas de profil, donc pas de score (cold start). "
                   "Chargez un scénario dans la barre latérale.")
    else:
        st.markdown("Posts aimés : " + ", ".join(f"**{x}**" for x in likes))
        top_terms = m.profile_weights(profile, top=12)
        st.bar_chart(pd.DataFrame(top_terms, columns=["terme", "poids"]).set_index("terme"),
                     horizontal=True, sort="-poids", height=330)
        show_code(FeedModel.build_profile)

        # 5. Scores
        st.markdown('<div class="step"><b>⑤ Score de similarité</b> — cosinus = Σ profil[t] × post[t] '
                    '(les deux vecteurs ont une longueur 1)</div>', unsafe_allow_html=True)
        contribs = m.term_contributions(profile, pid)
        score = float(m.similarity_scores(profile)[m.index[pid]])
        if pid in likes:
            st.info(f"{pid} est aimé : il fait partie du profil et est exclu du feed.")
        if contribs:
            st.dataframe(pd.DataFrame(contribs), hide_index=True, width="stretch",
                         column_config={c: st.column_config.NumberColumn(format="%.4f")
                                        for c in ["poids_profil", "poids_post", "contribution"]})
        st.markdown(f"Somme des contributions = **{fr(sum(c['contribution'] for c in contribs), 4)}** "
                    f"= score cosinus de scikit-learn **{fr(score, 4)}**")
        show_code(FeedModel.term_contributions)

        # 6. Classement
        st.markdown('<div class="step"><b>⑥ Classement</b> — posts non aimés, score décroissant '
                    '(égalité : identifiant)</div>', unsafe_allow_html=True)
        in_feed = {it.post_id: it.origine for it in feed.items}
        ranking = rank_by_similarity(m, likes)
        st.dataframe(pd.DataFrame([{
            "rang": r, "id": p, "titre": m.by_id[p]["titre"], "thème": m.by_id[p]["categorie"],
            "score de similarité": s, "dans le feed": in_feed.get(p, "—")}
            for r, (p, s) in enumerate(ranking, start=1)]),
            hide_index=True, width="stretch", height=300,
            column_config={"score de similarité": st.column_config.ProgressColumn(
                format="%.3f", min_value=0.0, max_value=max(s for _, s in ranking) or 1.0)})
        show_code(feed_module.rank_by_similarity)
        show_code(feed_module.build_feed)

    # Matrice
    st.markdown('<div class="step"><b>🧮 La matrice TF-IDF</b> — une ligne par post, une colonne '
                'par terme</div>', unsafe_allow_html=True)
    sel_rows = list(dict.fromkeys(likes + [it.post_id for it in feed.items[:5]] + [pid]))
    sel_terms = ([t for t, _ in m.profile_weights(profile, top=10)] if profile is not None
                 else [t for t, _ in m.post_weights(pid)[:10]])
    sub = pd.DataFrame(m.matrix[[m.index[r] for r in sel_rows]][:, [m.vectorizer.vocabulary_[t] for t in sel_terms]].toarray(),
                       index=sel_rows, columns=sel_terms)
    st.dataframe(styled_matrix(sub), width="stretch")
    st.caption(f"Sélection lisible : {len(sel_rows)} posts × {len(sel_terms)} termes. "
               f"La matrice complète fait {m.matrix.shape[0]} × {m.matrix.shape[1]} et contient "
               f"{m.matrix.nnz} valeurs non nulles ({100 * m.matrix.nnz / np.prod(m.matrix.shape):.1f} %).")
    if st.checkbox("Inspecter la matrice complète"):
        st.dataframe(pd.DataFrame(m.matrix.toarray(), index=m.ids, columns=m.terms).round(3),
                     width="stretch", height=420)

# --------------------------------------------------------------------------
# Onglet 3 — Expériences
# --------------------------------------------------------------------------
with tab_exp:
    ea, eb, ec, ed = st.tabs(["A · Textes → vecteurs", "B · Cosinus entre deux posts",
                              "C · Football puis voyage", "D · Avec / sans exploration"])

    with ea:
        st.markdown("Trois textes courts, vectorisés **seuls** (corpus de 3 documents) avec "
                    "**le même** `make_vectorizer()` que l'application.")
        cols = st.columns(3)
        texts = [cols[i].text_input(f"Texte {i + 1}", EXPERIENCE_A_TEXTS[i], key=f"exa_{i}")
                 for i in range(3)]
        for i, t in enumerate(texts):
            cols[i].markdown("".join(chip(x) for x in preprocess(t)) or "_aucun token_",
                             unsafe_allow_html=True)
        try:
            vec = make_vectorizer()
            X = vec.fit_transform(texts)
            names = [f"Texte {i + 1}" for i in range(3)]
            st.markdown("**Matrice TF-IDF (3 × vocabulaire)**")
            st.dataframe(styled_matrix(pd.DataFrame(X.toarray(), index=names,
                                                    columns=vec.get_feature_names_out())), width="stretch")
            st.markdown("**idf de chaque terme** — un terme présent dans 2 textes pèse moins.")
            st.dataframe(pd.DataFrame([vec.idf_], columns=vec.get_feature_names_out(), index=["idf"]).round(4),
                         width="stretch")
            st.markdown("**Similarités cosinus**")
            st.dataframe(styled_matrix(pd.DataFrame(cosine_similarity(X), index=names, columns=names)),
                         width="stretch")
        except ValueError:
            st.warning("Les textes ne contiennent aucun token utile (que des mots vides ?).")

    with eb:
        st.markdown("Le cosinus mesure le **vocabulaire partagé**, pas le « thème ».")
        pc = st.columns(len(EXPERIENCE_B_PAIRS))
        for i, (a, b, label) in enumerate(EXPERIENCE_B_PAIRS):
            if pc[i].button(f"{label} ({a} / {b})", key=f"pair_{i}", width="stretch"):
                st.session_state.exb_a, st.session_state.exb_b = a, b
        st.session_state.setdefault("exb_a", EXPERIENCE_B_PAIRS[0][0])
        st.session_state.setdefault("exb_b", EXPERIENCE_B_PAIRS[0][1])
        c1, c2 = st.columns(2)
        a = c1.selectbox("Publication A", m.ids, format_func=post_label, key="exb_a")
        b = c2.selectbox("Publication B", m.ids, format_func=post_label, key="exb_b")
        cos = m.cosine_between(a, b)
        st.metric("Similarité cosinus", fr(cos))
        shared = m.term_contributions(m.post_vector(a), b)
        if shared:
            st.dataframe(pd.DataFrame(shared).rename(columns={"poids_profil": f"poids dans {a}",
                                                              "poids_post": f"poids dans {b}"}),
                         hide_index=True, width="stretch")
        else:
            st.info("Aucun terme commun → cosinus = 0, même si les sujets se ressemblent.")
        show_code(FeedModel.cosine_between)

    with ec:
        before_likes = SCENARIOS["football"]["likes"]
        after_likes = SCENARIOS["football_voyage"]["likes"]
        before = [it.post_id for it in build_feed(m, before_likes).items]
        after_feed = build_feed(m, after_likes)
        after = [it.post_id for it in after_feed.items]
        scores_b = dict(rank_by_similarity(m, before_likes))
        scores_a = dict(rank_by_similarity(m, after_likes))
        st.markdown(f"**Avant** : likes {', '.join(before_likes)} · **Après** : + {after_likes[-1]} "
                    f"({m.by_id[after_likes[-1]]['titre']})")
        rows = []
        for p in dict.fromkeys(before + after):
            rb = before.index(p) + 1 if p in before else None
            ra = after.index(p) + 1 if p in after else None
            evo = ("🆕 entre" if rb is None else "❌ sort" if ra is None
                   else f"▲ {rb - ra}" if rb > ra else f"▼ {ra - rb}" if ra > rb else "=")
            rows.append({"id": p, "titre": m.by_id[p]["titre"], "thème": m.by_id[p]["categorie"],
                         "rang avant": rb, "score avant": scores_b.get(p),
                         "rang après": ra, "score après": scores_a.get(p), "évolution": evo})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
                     column_config={c: st.column_config.NumberColumn(format="%.3f")
                                    for c in ["score avant", "score après"]})
        c1, c2 = st.columns(2)
        for col, lk, title in [(c1, before_likes, "Profil avant"), (c2, after_likes, "Profil après")]:
            col.markdown(f"**{title}** (10 termes les plus lourds)")
            col.bar_chart(pd.DataFrame(m.profile_weights(m.build_profile(lk), 10),
                                       columns=["terme", "poids"]).set_index("terme"),
                          horizontal=True, sort="-poids", height=300)
        st.caption("Ajouter un like déplace la moyenne : les termes football pèsent un peu moins, "
                   "ceux du voyage apparaissent.")
        b1, b2 = st.columns(2)
        b1.button("Charger « avant » dans le feed", on_click=apply_scenario, args=("football",))
        b2.button("Charger « après » dans le feed", on_click=apply_scenario, args=("football_voyage",))

    with ed:
        lk = SCENARIOS["exploration"]["likes"]
        pct = st.slider("Exploration comparée (%)", 5, 50, EXPERIENCE_D_EXPLORATION, step=5, key="exd_pct")
        st.markdown(f"Likes : {', '.join(lk)} · feed de {FEED_SIZE} places.")
        c1, c2 = st.columns(2)
        for col, p_ in [(c1, 0), (c2, pct)]:
            r = build_feed(m, lk, p_ / 100)
            col.markdown(f"**Exploration {p_} %** — {r.exploration_obtenue} place(s)")
            col.dataframe(pd.DataFrame([{
                "rang": i, "id": it.post_id, "thème": m.by_id[it.post_id]["categorie"],
                "score de similarité": it.score, "origine": it.origine}
                for i, it in enumerate(r.items, start=1)]), hide_index=True, width="stretch",
                column_config={"score de similarité": st.column_config.NumberColumn(format="%.3f")})
            if p_:
                col.caption(f"Thèmes du top à 0 % : {', '.join(r.themes_du_top)} → "
                            f"thèmes absents : {', '.join(r.themes_absents) or 'aucun'}.")
        st.info("**Règle d'exploration** (séparée du NLP) : k = arrondi(8 × proportion) places. "
                "On parcourt les thèmes absents du top 8 de similarité dans l'ordre fixe "
                "football → voyage → cuisine → gaming → technologie → fitness et on prend, à tour de "
                "rôle, le meilleur post non aimé de chaque thème. Les scores ne sont pas modifiés ; "
                "les posts d'exploration sont insérés à intervalles réguliers.")
        show_code(feed_module.pick_exploration)
        st.button("Charger ce scénario dans le feed (25 %)", on_click=apply_scenario, args=("exploration",))

# --------------------------------------------------------------------------
# Onglet 4 — Comprendre & limites
# --------------------------------------------------------------------------
with tab_learn:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
### 🧠 Les notions
- **NLP** (traitement automatique du langage) : faire calculer une machine sur du texte.
- **Token** : une unité de texte, ici un mot en minuscules.
- **Mot vide (stopword)** : mot très fréquent et peu informatif (« le », « pour »), retiré.
- **TF-IDF** : un mot pèse lourd s'il est **fréquent dans le post** (TF) et **rare dans le corpus** (IDF).
- **Vecteur** : chaque post devient une liste de 564 nombres (un par terme du vocabulaire).
- **Cosinus** : mesure l'angle entre deux vecteurs. 1 = même direction, 0 = aucun mot commun.
""")
        st.markdown('<span class="formula">score(u, p) = cos(u, p) = Σ<sub>t</sub> u[t] × p[t]</span>',
                    unsafe_allow_html=True)
        st.markdown("""
### 🔀 Familles de recommandation
| Approche | Idée | Ici ? |
|---|---|---|
| **Basée sur le contenu** | « des posts qui *ressemblent* à ceux que vous aimez » | ✅ oui |
| **Filtrage collaboratif** | « des posts aimés par des *personnes qui vous ressemblent* » | ❌ un seul utilisateur |
| **Hybride** | combine les deux (+ popularité, contexte…) | ❌ |
""")
    with c2:
        syn = m.cosine_between("p01", "p07")
        rapide = next(c for c in m.term_contributions(m.build_profile(SCENARIOS["football"]["likes"]), "p18"))
        st.markdown(f"""
### ⚠️ Limites observables dans la démo
- **Cold start** : sans like, aucun profil → feed initial non personnalisé.
- **Vocabulaire** : un mot absent du corpus n'existe pas pour le modèle.
- **Synonymes** : « foot » ≠ « football ». cos(p01, p07) = **{fr(syn)}** malgré le même sport.
- **Polysémie** : les pâtes (p18) entrent dans le feed football grâce au seul mot
  « **{rapide['terme']}** » (contribution {fr(rapide['contribution'], 4)}).
- **Pas de lemmatisation** : « joueur » et « joueurs » sont deux termes différents.
- **Surspécialisation** : on recommande ce qui ressemble au passé ; l'exploration est un correctif simple.

### 🎯 Ce que le simulateur illustre — et ne prouve pas
✅ Il illustre un mécanisme réel et complet : texte → vecteurs → profil → cosinus → classement.

❌ Il ne reproduit **pas** l'algorithme de TikTok ou d'Instagram (qui utilisent des signaux
comportementaux massifs, des modèles appris, des objectifs d'engagement…).

❌ Une personnalisation de feed sur 40 posts fictifs et un utilisateur n'est **pas une preuve
scientifique** de bulle de filtre : il faudrait des utilisateurs réels, une durée, des mesures de
diversité et un protocole.

❌ Le score de similarité n'est **pas une probabilité d'aimer**.
""")

st.caption("Inside the Feed · données fictives · calcul local (scikit-learn), aucune API, aucun compte.")
