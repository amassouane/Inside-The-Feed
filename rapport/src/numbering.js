// Numérotation façon LaTeX (chapitres, sections, figures, tableaux, listings)
// + marqueurs invisibles utilisés par build.py pour retrouver les numéros de page.
(function () {
  const toc = [];
  let chap = 0, mk = 0;
  const marker = () => { const id = "@@K" + (++mk) + "@@"; const s = document.createElement("span"); s.className = "mk"; s.textContent = id; return [s, id]; };

  const PY_KW = /\b(def|return|if|else|for|in|not|and|or|import|from|class|None|True|False|self|as|with|lambda)\b/g;
  function highlight(line, lang) {
    if (lang === "sh") {
      const i = line.indexOf("#");
      return i >= 0 ? line.slice(0, i) + '<span class="com">' + line.slice(i) + "</span>" : line;
    }
    // Python : commentaires, chaînes, mots-clés (sur texte déjà échappé)
    let out = "", rest = line, m;
    const re = /("""[^]*?"""|r?"[^"]*"|#.*$)/;
    while ((m = re.exec(rest))) {
      out += rest.slice(0, m.index).replace(PY_KW, '<span class="kw">$1</span>');
      out += m[0].startsWith("#") ? '<span class="com">' + m[0] + "</span>" : '<span class="str">' + m[0] + "</span>";
      rest = rest.slice(m.index + m[0].length);
    }
    return out + rest.replace(PY_KW, '<span class="kw">$1</span>');
  }

  for (const sec of document.querySelectorAll("section.chapter")) {
    const h1 = sec.querySelector("h1");
    const title = h1.textContent.trim();
    const [m1, id1] = marker();
    if (sec.classList.contains("unnumbered")) {
      toc.push({ kind: "chap", num: "", title, mk: id1 });
    } else {
      chap++;
      h1.innerHTML = '<span class="chapno">Chapitre ' + chap + "</span>" + h1.innerHTML;
      toc.push({ kind: "chap", num: String(chap), title, mk: id1 });
    }
    h1.appendChild(m1);
    let s = 0, f = 0, t = 0, l = 0;
    for (const el of sec.querySelectorAll("h2, figure, table.bt, .listing")) {
      if (el.tagName === "H2") {
        s++;
        const num = chap + "." + s, t2 = el.textContent.trim();
        const [m2, id2] = marker();
        el.innerHTML = '<span class="secno">' + num + "</span> " + el.innerHTML;
        el.appendChild(m2);
        if (!sec.classList.contains("unnumbered")) toc.push({ kind: "sec", num, title: t2, mk: id2 });
      } else if (el.tagName === "FIGURE") {
        f++;
        const num = chap + "." + f, cap = el.dataset.caption;
        const [m3, id3] = marker();
        const c = document.createElement("div"); c.className = "caption";
        c.innerHTML = '<span class="tag">Figure ' + num + "</span> – " + cap; c.appendChild(m3);
        el.appendChild(c);
        toc.push({ kind: "fig", num, title: cap.replace(/&amp;/g, "&"), mk: id3 });
      } else if (el.tagName === "TABLE") {
        t++;
        const c = document.createElement("div"); c.className = "caption";
        c.innerHTML = '<span class="tag">Table ' + chap + "." + t + "</span> – " + el.dataset.caption;
        el.after(c);
      } else {
        l++;
        const pre = el.querySelector("pre"), lang = pre.dataset.lang;
        pre.innerHTML = pre.innerHTML.split("\n").map((ln, i) => '<span class="ln">' + (i + 1) + "</span>" + highlight(ln, lang)).join("\n");
        const c = document.createElement("div"); c.className = "caption";
        c.textContent = "Listing " + chap + "." + l + " – " + el.dataset.caption;
        el.appendChild(c);
      }
    }
  }
  window.__toc = toc;
})();
