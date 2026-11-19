"""Génère les PDF de la présentation à partir du diaporama HTML.

  presentation/Presentation_InsideTheFeed.pdf        une page par diapo, tous les éléments révélés
  presentation/Guide_Presentation_InsideTheFeed.pdf  guide du binôme (guide.html + fiches diapo)

Prérequis : pip install playwright pypdfium2 pillow  (Chromium de Playwright, ou Google Chrome)
Usage     : python presentation/src/build.py && python presentation/src/build_pdfs.py
"""
from __future__ import annotations

import html
import re
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

SRC = Path(__file__).resolve().parent
DECK = SRC.parent / "Presentation_InsideTheFeed.html"
SHOTS = SRC / "shots"
DECK_PDF = SRC.parent / "Presentation_InsideTheFeed.pdf"
GUIDE_PDF = SRC.parent / "Guide_Presentation_InsideTheFeed.pdf"

# Minutage indicatif (minutes) de chaque diapo, pour une présentation de 25 min.
DUREES = {1: .5, 2: 1, 3: .5, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1.5, 9: 1.25, 10: 1.25, 11: 1, 12: 1.25, 13: .75,
          14: 1, 15: 1, 16: 4, 17: 2, 18: 1, 19: 1.25, 20: .75, 21: .75, 22: .25}
PASSAGES = {10: ("", "↪ <b>Changement 1 (A → M)</b> — « Le texte est devenu un vecteur. Mais comment l'utilisateur devient-il un vecteur ? Alaa Eddine va vous le montrer. »"),
            16: ("", "▶ <b>Démo en direct</b> — M passe à l'application (<kbd>⌘2</kbd>) et suit la partie 4 ; retour au diaporama (<kbd>⌘1</kbd>) pour la diapo 17."),
            18: (" toA", "↪ <b>Changement 2 (M → A)</b> — « Le moteur est vérifié. Mais il a des limites : Abdelati va vous les présenter. »"),
            20: ("", "↪ <b>Changement 3 (A → M)</b> — « Alaa Eddine, pour conclure. »")}
FOOTER = ('<div style="font-size:7pt;color:#8a90a2;width:100%;padding:0 15mm;display:flex;justify-content:space-between">'
          '<span>{label}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')


def launch(pw):
    try:
        return pw.chromium.launch()
    except Exception:  # Chromium de Playwright absent : on utilise Google Chrome
        return pw.chromium.launch(channel="chrome")


def shoot(browser) -> int:
    """Une capture par diapo, tous les fragments révélés et animations terminées."""
    SHOTS.mkdir(exist_ok=True)
    page = browser.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=2)
    page.goto(DECK.as_uri())
    n = page.evaluate("document.querySelectorAll('section.slide').length")
    for k in range(1, n + 1):
        page.goto(f"{DECK.as_uri()}#{k}")
        page.reload()
        page.wait_for_timeout(300)
        page.add_style_tag(content="#hint{display:none!important}")
        for _ in range(page.evaluate("document.querySelector('section.slide.active').querySelectorAll('.f').length")):
            page.keyboard.press("ArrowRight")
            page.wait_for_timeout(60)
        page.wait_for_timeout(1700)
        png = SHOTS / f"s{k:02d}.png"
        page.screenshot(path=str(png))
        Image.open(png).convert("RGB").save(png.with_suffix(".jpg"), quality=88)
        png.unlink()
    page.close()
    return n


def deck_pdf(browser, n: int) -> None:
    imgs = "".join(f'<img src="{(SHOTS / f"s{k:02d}.jpg").as_uri()}">' for k in range(1, n + 1))
    tmp = SHOTS / "_deck.html"  # fichier local : une page about:blank ne peut pas charger d'images file://
    tmp.write_text("<style>@page{size:1280px 720px;margin:0}body{margin:0}"
                   "img{width:1280px;height:720px;display:block;break-after:page}</style>" + imgs, encoding="utf-8")
    page = browser.new_page()
    page.goto(tmp.as_uri())
    page.wait_for_load_state("networkidle")
    page.pdf(path=str(DECK_PDF), width="1280px", height="720px", print_background=True)
    page.close()
    tmp.unlink()


def slide_cards(n: int) -> str:
    """Fiches « diapo par diapo » générées depuis les titres et les notes orales des diapos."""
    src = (SRC / "slides.html").read_text(encoding="utf-8")
    sections = re.findall(r"<section(.*?)</section>", src, re.S)[:n]
    out, t = [], 0.0
    for k, s in enumerate(sections, 1):
        title = re.search(r"<h[12][^>]*>(.*?)</h[12]>", s, re.S)
        title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", title.group(1))).strip() if title else "Conclusion"
        notes = html.unescape(re.search(r'data-notes="([^"]*)"', s).group(1))
        who = "AM" if k == 22 else ("A" if notes.startswith("(A)") else "M")
        notes = re.sub(r"^\((A|M)\)\s*", "", notes)
        d = DUREES.get(k, 1)
        mm, ss = divmod(int(round(t * 60)), 60)
        out.append(f'<div class="slide"><img src="shots/s{k:02d}.jpg"><div><div class="hd"><span class="n">{k}</span>'
                   f'<span class="ti">{html.escape(title)}</span><span class="tag {who}">{"A + M" if who == "AM" else who}</span>'
                   f'<span class="dur">{mm}:{ss:02d} · {d:g} min</span></div>'
                   f'<p class="say">« {html.escape(notes)} »</p></div></div>')
        if k in PASSAGES:
            cls, txt = PASSAGES[k]
            out.append(f'<div class="handover{cls}">{txt}</div>')
        t += d
    return "\n".join(out)


def guide_pdf(browser, n: int) -> None:
    tmp = SRC / "_guide.html"
    tmp.write_text((SRC / "guide.html").read_text(encoding="utf-8").replace("<!--SLIDES-->", slide_cards(n)), encoding="utf-8")
    page = browser.new_page()
    page.goto(tmp.as_uri())
    page.wait_for_load_state("networkidle")
    page.pdf(path=str(GUIDE_PDF), format="A4", print_background=True, prefer_css_page_size=True,
             display_header_footer=True, header_template="<span></span>",
             footer_template=FOOTER.format(label="Inside the Feed · Guide de présentation · Binôme 10"))
    page.close()
    tmp.unlink()


def main() -> None:
    with sync_playwright() as pw:
        browser = launch(pw)
        n = shoot(browser)
        deck_pdf(browser, n)
        guide_pdf(browser, n)
        browser.close()
    print(f"{DECK_PDF} ({n} pages)\n{GUIDE_PDF}")


if __name__ == "__main__":
    main()
