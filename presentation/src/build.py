"""Assemble presentation/Presentation_InsideTheFeed.html (fichier unique, images intégrées).

Usage : python presentation/src/build.py
"""
import base64
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent
OUT = SRC.parent / "Presentation_InsideTheFeed.html"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def inline(match: re.Match) -> str:
    path = (SRC / match.group(1)).resolve()
    data = base64.b64encode(path.read_bytes()).decode()
    return f'src="data:{MIME[path.suffix]};base64,{data}"'


html = (SRC / "slides.html").read_text(encoding="utf-8")
html = re.sub(r'src="(\.\./[^"]+)"', inline, html)
OUT.write_text(html, encoding="utf-8")
print(f"{OUT} ({OUT.stat().st_size // 1024} Ko)")
