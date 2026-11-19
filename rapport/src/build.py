"""Génère rapport/Rapport_InsideTheFeed.pdf à partir de cover.html, body.html et style.css.

Prérequis : pip install playwright pypdfium2  (Chromium installé par Playwright)
Usage     : python rapport/src/build.py
"""
from __future__ import annotations

import html
import re
import sys
import tempfile
from pathlib import Path

import pypdfium2 as pdfium
from playwright.sync_api import sync_playwright

SRC = Path(__file__).resolve().parent
OUT = SRC.parent / "Rapport_InsideTheFeed.pdf"


def render(page, html_path: Path, pdf_path: Path) -> None:
    page.goto(html_path.as_uri())
    page.wait_for_load_state("networkidle")
    page.pdf(path=str(pdf_path), prefer_css_page_size=True, print_background=True)


def marker_pages(pdf_path: Path) -> dict[str, int]:
    found: dict[str, int] = {}
    doc = pdfium.PdfDocument(str(pdf_path))
    for i in range(len(doc)):
        text = doc[i].get_textpage().get_text_range()
        for m in re.findall(r"@@K\d+@@", text.replace("\r", "").replace("\n", "")):
            found.setdefault(m, i + 1)
    return found


def toc_row(cls: str, num: str, title: str, page: int, dots: bool = True) -> str:
    return (f'<div class="toc-row {cls}"><span class="lbl"><span class="num">{html.escape(num)}</span>'
            f'{html.escape(title)}</span><span class="dots"{"" if dots else " style=border:0"}></span>'
            f'<span class="pg">{page}</span></div>')


def front_html(toc: list[dict], pages: dict[str, int]) -> str:
    rows, figs = [], []
    for e in toc:
        p = pages.get(e["mk"], "?")
        if e["kind"] == "chap":
            rows.append(toc_row("l1", e["num"], e["title"], p))
        elif e["kind"] == "sec":
            rows.append(toc_row("l2", e["num"], e["title"], p))
        else:
            figs.append(toc_row("", e["num"], e["title"], p))
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<link rel="stylesheet" href="style.css"></head><body><div class="front">
<div class="front-page"><h1>Table des matières</h1>{''.join(rows)}</div>
<div class="front-page lof"><h1>Table des figures</h1>{''.join(figs)}</div>
</div></body></html>"""


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp, sync_playwright() as pw:
        tmp = Path(tmp)
        browser = pw.chromium.launch()
        page = browser.new_page()
        render(page, SRC / "cover.html", tmp / "cover.pdf")
        render(page, SRC / "body.html", tmp / "body.pdf")
        toc = page.evaluate("window.__toc")
        pages = marker_pages(tmp / "body.pdf")
        missing = [e["title"] for e in toc if e["mk"] not in pages]
        if missing:
            print("Marqueurs introuvables :", missing, file=sys.stderr)
        front = SRC / "_front.html"
        front.write_text(front_html(toc, pages), encoding="utf-8")
        render(page, front, tmp / "front.pdf")
        front.unlink()
        browser.close()

        merged = pdfium.PdfDocument.new()
        for part in ("cover", "front", "body"):
            merged.import_pages(pdfium.PdfDocument(str(tmp / f"{part}.pdf")))
        merged.save(str(OUT))
        print(f"{OUT} — {len(merged)} pages")


if __name__ == "__main__":
    main()
