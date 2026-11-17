#!/usr/bin/env python3
"""Pre-render the menu, reviews and structured data into the HTML pages.

The JSON files stay the one place you edit. This script writes the finished
HTML into the pages, so search engines and AI crawlers read real dishes
instead of "Loading menu...".

Usage:
  python3 scripts/build.py          # rewrite the pages
  python3 scripts/build.py --check  # exit 1 if the pages are out of date

Standard library only. Run it after editing anything in data/ or
cheap-date-nights/data/, then commit the changed files.
"""
import json
import re
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://theblueheron.restaurant"


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def esc(value):
    return escape(str(value or "").strip(), quote=True)


# ---------- menu HTML (same markup and classes the page already styles) ----------

def item_html(item, show_pairings=False):
    out = [
        '<div class="menu-item">',
        '<div class="menu-item-row">',
        f'<h3 class="menu-item-title">{esc(item.get("name"))}</h3>',
        '<span class="menu-item-dots"></span>',
        f'<span class="menu-item-price">{esc(item.get("price"))}</span>',
        "</div>",
        f'<span class="menu-item-desc">{esc(item.get("description"))}</span>',
    ]
    pairings = item.get("pairings") or []
    if show_pairings and pairings:
        rows = []
        for p in pairings:
            extra = f' <span>— {esc(p.get("description"))}</span>' if p.get("description") else ""
            rows.append(
                f'<div class="pairing"><strong>{esc(p.get("label"))}</strong> {esc(p.get("name"))}{extra}</div>'
            )
        out.append('<div class="pairings">' + "".join(rows) + "</div>")
    out.append("</div>")
    return "".join(out)


def block_html(section, show_pairings=False):
    items = "".join(item_html(i, show_pairings) for i in section.get("items", []))
    return (
        '<section class="menu-block"><div class="menu-header">'
        f'<h2>{esc(section.get("title"))}</h2>'
        f'<div class="menu-subtitle">{esc(section.get("subtitle"))}</div></div>'
        f'<div class="menu-grid">{items}</div></section>'
    )


def home_menu_html(sections):
    parts = []
    for i, s in enumerate(sections):
        top = "none" if i == 0 else "1px solid rgba(0,65,105,0.1)"
        pad = "0" if i == 0 else "70px"
        items = "".join(item_html(x) for x in s.get("items", []))
        parts.append(
            f'<section class="section-padding menu-preview" style="border-top:{top};padding-top:{pad};padding-bottom:0">'
            f'<div class="menu-header"><h2>{esc(s.get("title"))}</h2>'
            f'<div class="menu-subtitle">{esc(s.get("subtitle"))}</div></div>'
            f'<div class="menu-grid" style="text-align:left">{items}</div></section>'
        )
    return "\n".join(parts)


def reviews_html(reviews):
    parts = []
    for r in reviews:
        stars = "★" * int(r.get("rating", 5))
        parts.append(
            '<article class="review-card"><div class="review-header">'
            f'<img class="review-avatar" src="{esc(r.get("image"))}" alt="{esc(r.get("name"))} Google review profile photo" loading="lazy">'
            f'<div><h3 class="review-name">{esc(r.get("name"))}</h3>'
            f'<p class="review-meta">{esc(r.get("date"))}</p></div></div>'
            f'<div class="review-stars" aria-label="{int(r.get("rating", 5))} out of 5 stars">{stars}</div>'
            f'<p class="review-text">“{esc(r.get("text"))}”</p>'
            f'<a class="review-link" href="{esc(r.get("link"))}" target="_blank" rel="noopener noreferrer">Read on Google</a>'
            "</article>"
        )
    return "\n".join(parts)


# ---------- structured data ----------

def schema_menu(sections):
    out = []
    for s in sections:
        items = []
        for it in s.get("items", []):
            name = it.get("name", "")
            clean = re.sub(r"\s*\(v\)|\*", "", name).strip()
            mi = {"@type": "MenuItem", "name": clean}
            if (it.get("description") or "").strip():
                mi["description"] = it["description"].strip()
            prices = re.findall(r"\$(\d+(?:\.\d{1,2})?)", it.get("price") or "")
            offers = [{"@type": "Offer", "price": p, "priceCurrency": "USD"} for p in prices]
            if len(offers) == 1:
                mi["offers"] = offers[0]
            elif offers:
                mi["offers"] = offers
            if "(v)" in name:
                mi["suitableForDiet"] = "https://schema.org/VegetarianDiet"
            items.append(mi)
        out.append({"@type": "MenuSection", "name": s.get("title", ""), "hasMenuItem": items})
    return {
        "@type": "Menu",
        "name": "Dinner Menu",
        "url": f"{SITE}/#menu",
        "inLanguage": "en-US",
        "hasMenuSection": out,
    }


# ---------- page patching ----------

def replace_between(html, name, content, path):
    pattern = re.compile(rf"(<!-- {name}:START -->)(.*?)(<!-- {name}:END -->)", re.S)
    if not pattern.search(html):
        sys.exit(f"{path}: missing <!-- {name}:START --> / <!-- {name}:END --> markers")
    return pattern.sub(lambda m: f"{m.group(1)}\n{content}\n{m.group(3)}", html, count=1)


def set_text_by_id(html, element_id, text, path):
    pattern = re.compile(rf'(<(\w+)[^>]*\sid="{element_id}"[^>]*>)(.*?)(</\2>)', re.S)
    if not pattern.search(html):
        sys.exit(f'{path}: no element with id="{element_id}"')
    return pattern.sub(lambda m: f"{m.group(1)}{esc(text)}{m.group(4)}", html, count=1)


def build_home():
    path = ROOT / "index.html"
    html = path.read_text(encoding="utf-8")
    sections = load("data/menu.json")
    sections = sections if isinstance(sections, list) else sections.get("sections", [])
    html = replace_between(html, "MENU", home_menu_html(sections), path)
    html = replace_between(html, "REVIEWS", reviews_html(load("data/reviews.json")), path)

    restaurant = load("data/restaurant.json")
    restaurant["hasMenu"] = schema_menu(sections)
    ld = json.dumps(restaurant, indent=2, ensure_ascii=False).replace("</", "<\\/")
    pattern = re.compile(r'(<script type="application/ld\+json" id="restaurant-ld">)(.*?)(</script>)', re.S)
    if not pattern.search(html):
        sys.exit(f'{path}: missing <script type="application/ld+json" id="restaurant-ld">')
    html = pattern.sub(lambda m: f"{m.group(1)}\n{ld}\n{m.group(3)}", html, count=1)
    return path, html


def build_cheap_date():
    path = ROOT / "cheap-date-nights" / "index.html"
    html = path.read_text(encoding="utf-8")
    cheap = load("cheap-date-nights/data/cheap-date-menu.json")
    dinner = load("data/menu.json")
    dinner = dinner if isinstance(dinner, list) else dinner.get("sections", [])

    html = replace_between(html, "CHEAP", "".join(block_html(s, True) for s in cheap.get("sections", [])), path)
    html = replace_between(html, "MENU", "".join(block_html(s) for s in dinner), path)
    html = set_text_by_id(html, "hero-dates", cheap.get("subtitle") or "This week's menu", path)
    html = set_text_by_id(html, "weekly-date", cheap.get("subtitle") or "", path)
    html = set_text_by_id(html, "weekly-price", cheap.get("price") or "$50 for Two", path)
    if cheap.get("description"):
        html = set_text_by_id(html, "how-description", cheap["description"], path)
    return path, html


def main():
    check = "--check" in sys.argv
    stale = []
    for path, new in (build_home(), build_cheap_date()):
        old = path.read_text(encoding="utf-8")
        if old != new:
            stale.append(path.relative_to(ROOT))
            if not check:
                path.write_text(new, encoding="utf-8")
    if check and stale:
        print("Out of date. Run: python3 scripts/build.py")
        for p in stale:
            print("  ", p)
        sys.exit(1)
    print("Updated: " + ", ".join(map(str, stale)) if stale else "Already up to date.")


if __name__ == "__main__":
    main()
