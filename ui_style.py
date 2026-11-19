"""Apparence de l'interface : couleurs, visuels locaux et HTML des cartes.

Aucun calcul ici. Les visuels sont des dégradés CSS + emojis : rien n'est
téléchargé, tout fonctionne hors ligne.
"""
from __future__ import annotations

from html import escape

CATEGORY_STYLE = {
    "football":    {"emoji": "⚽", "label": "Football",    "c1": "#0f9d58", "c2": "#0b5d3b"},
    "voyage":      {"emoji": "✈️", "label": "Voyage",      "c1": "#1e88e5", "c2": "#0d47a1"},
    "cuisine":     {"emoji": "🍳", "label": "Cuisine",     "c1": "#fb8c00", "c2": "#c43e00"},
    "gaming":      {"emoji": "🎮", "label": "Gaming",      "c1": "#8e24aa", "c2": "#4a148c"},
    "technologie": {"emoji": "💻", "label": "Technologie", "c1": "#00897b", "c2": "#004d40"},
    "fitness":     {"emoji": "💪", "label": "Fitness",     "c1": "#e53935", "c2": "#8e0000"},
}

# Hashtags qui signalent un second thème (posts « mixtes »), pour le visuel.
HASHTAG_THEME = {
    "#football": "football", "#foot": "football", "#voyage": "voyage",
    "#cuisine": "cuisine", "#recette": "cuisine", "#gaming": "gaming",
    "#technologie": "technologie", "#fitness": "fitness",
}


def fr(x: float, digits: int = 3) -> str:
    """Nombre au format français (virgule décimale)."""
    return f"{x:.{digits}f}".replace(".", ",")


def secondary_emojis(post: dict) -> str:
    themes = {HASHTAG_THEME[h] for h in post["hashtags"] if h in HASHTAG_THEME}
    themes.discard(post["categorie"])
    return "".join(CATEGORY_STYLE[t]["emoji"] for t in sorted(themes))


def card_html(post: dict, rank: int, score: float | None, origine: str,
              move: str = "", liked: bool = False) -> str:
    s = CATEGORY_STYLE[post["categorie"]]
    badges = []
    if origine == "initial":
        badges.append('<span class="badge neutral">Feed initial · non personnalisé</span>')
    elif score is not None:
        badges.append(f'<span class="badge score">Score de similarité {fr(score)}</span>')
    if origine == "exploration":
        badges.append('<span class="badge explore">🧭 Exploration</span>')
    if liked:
        badges.append('<span class="badge liked">❤️ Aimé</span>')
    if move:
        badges.append(f'<span class="badge move">{escape(move)}</span>')
    tags = "".join(f'<span class="tag">{escape(h)}</span>' for h in post["hashtags"])
    return f"""
<div class="banner" style="background:linear-gradient(135deg,{s['c1']},{s['c2']})">
  <span class="rank">#{rank}</span>
  <span class="big-emoji">{s['emoji']}</span><span class="mini-emoji">{secondary_emojis(post)}</span>
  <span class="cat">{s['label']}</span>
</div>
<div class="title">{escape(post['titre'])}</div>
<div class="author">{escape(post['auteur'])} · {post['id']} · <i>fictif</i></div>
<div class="desc">{escape(post['description'])}</div>
<div class="tags">{tags}</div>
<div class="badges">{''.join(badges)}</div>
"""


def chip(text: str, kind: str = "token") -> str:
    return f'<span class="chip {kind}">{escape(text)}</span>'


def css(presentation: bool) -> str:
    base = "19px" if presentation else "16px"
    return f"""
<style>
html {{ font-size: {base}; }}
.block-container {{ padding-top: 1.6rem; max-width: 1400px; }}
.hero {{ background: linear-gradient(120deg,#111827,#1f2937 55%,#312e81);
  color:#fff; border-radius:18px; padding:1.1rem 1.5rem; margin-bottom:1rem; }}
.hero h1 {{ color:#fff; margin:0; font-size:2.1rem; letter-spacing:-.5px; }}
.hero p {{ margin:.25rem 0 0 0; opacity:.85; }}
.banner {{ position:relative; height:118px; border-radius:12px; margin-bottom:.6rem;
  display:flex; align-items:center; justify-content:center; overflow:hidden; }}
.big-emoji {{ font-size:3.4rem; filter:drop-shadow(0 4px 6px rgba(0,0,0,.3)); }}
.mini-emoji {{ font-size:1.6rem; margin-left:.4rem; align-self:flex-end; margin-bottom:.6rem; }}
.rank {{ position:absolute; top:8px; left:12px; color:#fff; font-weight:800; font-size:1.3rem; }}
.cat {{ position:absolute; bottom:8px; right:12px; color:#fff; font-size:.75rem; font-weight:700;
  text-transform:uppercase; letter-spacing:1px; background:rgba(0,0,0,.25); padding:2px 8px; border-radius:20px; }}
.title {{ font-weight:750; font-size:1.12rem; line-height:1.25; margin-bottom:.15rem; }}
.author {{ color:#6b7280; font-size:.8rem; margin-bottom:.35rem; }}
.desc {{ font-size:.9rem; color:#374151; margin-bottom:.4rem; }}
.tag {{ display:inline-block; color:#4338ca; background:#eef2ff; border-radius:6px;
  padding:1px 6px; margin:0 4px 4px 0; font-size:.8rem; }}
.badges {{ margin:.2rem 0 .3rem 0; }}
.badge {{ display:inline-block; border-radius:20px; padding:2px 10px; margin:0 4px 4px 0;
  font-size:.8rem; font-weight:650; }}
.badge.score {{ background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; }}
.badge.neutral {{ background:#f3f4f6; color:#374151; border:1px solid #d1d5db; }}
.badge.explore {{ background:#fff7ed; color:#9a3412; border:1px solid #fdba74; }}
.badge.liked {{ background:#fdf2f8; color:#9d174d; border:1px solid #f9a8d4; }}
.badge.move {{ background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe; }}
.chip {{ display:inline-block; border-radius:8px; padding:2px 8px; margin:0 5px 6px 0;
  font-family:ui-monospace,Menlo,monospace; font-size:.85rem; }}
.chip.token {{ background:#e0e7ff; color:#3730a3; }}
.chip.stop {{ background:#f3f4f6; color:#9ca3af; text-decoration:line-through; }}
.chip.term {{ background:#dcfce7; color:#166534; }}
.step {{ background:#f8fafc; border-left:5px solid #6366f1; border-radius:10px;
  padding:.7rem 1rem; margin:.6rem 0; }}
.tour {{ background:linear-gradient(120deg,#eef2ff,#fdf4ff); border:1px solid #c7d2fe;
  border-radius:16px; padding:1rem 1.3rem; margin-bottom:1rem; }}
.tour h3 {{ margin:0 0 .4rem 0; }}
.formula {{ font-family:ui-monospace,Menlo,monospace; background:#111827; color:#e5e7eb;
  border-radius:10px; padding:.6rem 1rem; display:inline-block; }}
</style>
"""
