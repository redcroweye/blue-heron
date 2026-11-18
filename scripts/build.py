#!/usr/bin/env python3
"""Build the Blue Heron website.

Reads the content in data/ and the page templates in src/, and writes the
finished pages into docs/ (the folder GitHub Pages serves).

Usage:
  python3 scripts/build.py          # rebuild the pages
  python3 scripts/build.py --check  # exit 1 if docs/ is out of date

Standard library only. Python 3.8 or newer.
"""
import json
import re
import sys
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC = ROOT / "src"
OUT = ROOT / "docs"

# (output file, template name, nav label or None, title, description)
PAGES = [
    ("index.html", "home", None,
     "The Blue Heron | Relaxed Dining, Refined Cuisine in Rapid City, South Dakota",
     "The Blue Heron offers chef-driven American cuisine, curated wines, handcrafted cocktails, and refined dining in Rapid City, South Dakota, at the western entrance to the Black Hills."),
    ("menu/index.html", "menu", "Menu",
     "Dinner Menu | The Blue Heron, Rapid City, SD",
     "The dinner menu at The Blue Heron in Rapid City: starters, entrées and sides made from scratch with French technique and Northern Great Plains ingredients."),
    ("cheap-date-night/index.html", "cheap-date-night", "Cheap Date Night",
     "Cheap Date Night in Rapid City | The Blue Heron",
     "Cheap Date Night at The Blue Heron in Rapid City: a midweek dinner for two with paired wine or beer, plus the full dinner menu."),
    ("visiting-the-black-hills/index.html", "visiting", "Visit",
     "Dinner Near Mount Rushmore and the Black Hills | The Blue Heron, Rapid City",
     "Looking for dinner near Mount Rushmore, Crazy Horse or Custer State Park? The Blue Heron is in Rapid City at the western entrance to the Black Hills."),
    ("private-events/index.html", "private-events", "Private Events",
     "Private Events and Group Dining | The Blue Heron, Rapid City",
     "Private dining is coming soon to The Blue Heron in Rapid City. Contact us about rehearsal dinners, birthdays and company dinners."),
    ("reservations/index.html", "reservations", None,
     "Reservations, Hours and Location | The Blue Heron, Rapid City",
     "Reserve a table at The Blue Heron, 740 Mountain View Road, Rapid City. Dinner Tuesday to Saturday. Call (605) 416-9804."),
]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def e(value):
    return escape(str(value if value is not None else "").strip(), quote=True)


# ---------- content blocks ----------

def menu_item(item, pairings=False):
    out = (
        '<div class="menu-item"><div class="menu-item-row">'
        f'<h3 class="menu-item-title">{e(item.get("name"))}</h3>'
        '<span class="menu-item-dots" aria-hidden="true"></span>'
        f'<span class="menu-item-price">{e(item.get("price"))}</span></div>'
        f'<span class="menu-item-desc">{e(item.get("description"))}</span>'
    )
    pairs = item.get("pairings") or []
    if pairings and pairs:
        rows = []
        for p in pairs:
            extra = f' <span>&mdash; {e(p.get("description"))}</span>' if p.get("description") else ""
            rows.append(f'<div class="pairing"><strong>{e(p.get("label"))}</strong> {e(p.get("name"))}{extra}</div>')
        out += '<div class="pairings">' + "".join(rows) + "</div>"
    return out + "</div>"


def menu_blocks(sections, pairings=False):
    out = []
    for s in sections:
        items = "\n".join(menu_item(i, pairings) for i in s.get("items", []))
        sub = f'<p class="section-sub">{e(s.get("subtitle"))}</p>' if s.get("subtitle") else '<p class="section-sub" aria-hidden="true"></p>'
        out.append(
            f'<div class="menu-block"><h2 class="section-title">{e(s.get("title"))}</h2>{sub}'
            f'<div class="menu-grid">\n{items}\n</div></div>'
        )
    return "\n".join(out)


def review_cards(reviews):
    out = []
    for r in reviews:
        name = r.get("name", "")
        rating = int(r.get("rating", 5))
        out.append(
            '<article class="review"><div class="review-head">'
            f'<div class="avatar" aria-hidden="true">{e(name[:1])}</div>'
            f'<div><div class="review-name">{e(name)}</div><div class="review-src">{e(r.get("date") or "Google Review")}</div></div></div>'
            f'<div class="stars" role="img" aria-label="{rating} out of 5 stars">{"★" * rating}</div>'
            f'<p class="review-text">“{e(r.get("text"))}”</p></article>'
        )
    return "\n".join(out)


def social_cards(links):
    return "\n".join(
        f'<a class="social-card" href="{e(s["url"])}" target="_blank" rel="noopener noreferrer">'
        f'<h3>{e(s["name"])}</h3><p>{e(s["blurb"])}</p></a>'
        for s in links
    )


def drive_rows(visitors):
    return "\n".join(
        f'<div class="row"><span>{e(s["name"])}</span><span class="when">{e(s["time"])}</span></div>'
        for s in visitors.get("sights", [])
    )


def hours_location(site):
    h = site["hours"]
    return f"""<section class="info section" id="hours">
  <div class="container info-grid">
    <div>
      <h2>Dinner Service</h2>
      <p>{e(h["days"])}</p>
      <p>Open &ndash; {e(h["opens"])}</p>
      <p>Last Seating &ndash; {e(h["lastSeating"])}</p>
      <p class="gold">{e(site["reservationNote"])}</p>
      <p class="gold">{e(site["dressNote"])}</p>
      <p class="gold">{e(site["serviceAnimalNote"])}</p>
    </div>
    <div>
      <h2>The Location</h2>
      <p>{e(site["street"])}</p>
      <p>{e(site["city"])}, {e(site["region"])} {e(site["zip"])}</p>
      <p style="opacity:.65;font-size:.85rem">({e(site["locationNote"])})</p>
      <a class="btn btn-light" href="{e(site["directionsUrl"])}" target="_blank" rel="noopener noreferrer">Get Directions</a>
    </div>
    <div>
      <h2>Connect</h2>
      <p>Phone: <a href="tel:{e(site["phoneDigits"])}">{e(site["phone"])}</a></p>
      <a class="btn btn-light" href="tel:{e(site["phoneDigits"])}">Call for Reservations</a>
      <p style="margin-top:20px">Email: {e(site["email"])}</p>
      <a class="btn btn-light" href="mailto:{e(site["email"])}">Email for inquiries</a>
    </div>
  </div>
</section>"""


# ---------- structured data ----------

def restaurant_schema(site):
    s = site
    d = {
        "@context": "https://schema.org",
        "@type": "Restaurant",
        "name": s["name"],
        "url": s["siteUrl"],
        "telephone": s["phoneDigits"],
        "email": s["email"],
        "priceRange": s["priceRange"],
        "servesCuisine": s["cuisine"],
        "acceptsReservations": True,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": s["street"],
            "addressLocality": s["city"],
            "addressRegion": s["region"],
            "postalCode": s["zip"],
            "addressCountry": "US",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": s["latitude"], "longitude": s["longitude"]},
        "sameAs": [x["url"] for x in s["social"] if "maps.google" not in x["url"]],
        "menu": s["siteUrl"].rstrip("/") + "/menu/",
    }
    h = s["hours"]
    if h.get("schemaCloses"):
        d["openingHoursSpecification"] = [{
            "@type": "OpeningHoursSpecification",
            "dayOfWeek": h["schemaDays"],
            "opens": h["schemaOpens"],
            "closes": h["schemaCloses"],
        }]
    return d


def menu_schema(sections, site):
    out = []
    for s in sections:
        items = []
        for it in s.get("items", []):
            name = it.get("name", "")
            mi = {"@type": "MenuItem", "name": re.sub(r"\s*\(v\)|\*", "", name).strip()}
            if (it.get("description") or "").strip():
                mi["description"] = it["description"].strip()
            offers = [{"@type": "Offer", "price": p, "priceCurrency": "USD"}
                      for p in re.findall(r"\$(\d+(?:\.\d{1,2})?)", it.get("price") or "")]
            if len(offers) == 1:
                mi["offers"] = offers[0]
            elif offers:
                mi["offers"] = offers
            if "(v)" in name:
                mi["suitableForDiet"] = "https://schema.org/VegetarianDiet"
            items.append(mi)
        out.append({"@type": "MenuSection", "name": s.get("title", ""), "hasMenuItem": items})
    return {
        "@context": "https://schema.org",
        "@type": "Menu",
        "name": "Dinner Menu",
        "url": site["siteUrl"].rstrip("/") + "/menu/",
        "inLanguage": "en-US",
        "hasMenuSection": out,
    }


def ld_tag(obj):
    body = json.dumps(obj, indent=2, ensure_ascii=False).replace("</", "<\\/")
    return f'<script type="application/ld+json">\n{body}\n</script>'


# ---------- assembly ----------

def fill(template, values, where):
    def sub(m):
        key = m.group(1)
        if key not in values:
            sys.exit(f"{where}: unknown placeholder {{{{{key}}}}}")
        return values[key]
    return re.sub(r"\{\{\s*([a-z_0-9]+)\s*\}\}", sub, template)


def find_photo(stem):
    for ext in ("jpg", "jpeg", "webp", "png"):
        p = OUT / "assets" / "photos" / f"{stem}.{ext}"
        if p.exists():
            return f"assets/photos/{p.name}"
    return None


def build():
    site = load("site.json")
    menu = load("menu.json")
    menu = menu if isinstance(menu, list) else menu.get("sections", [])
    reviews = load("reviews.json")
    cheap = load("cheap-date.json")
    visitors = load("visitors.json")
    layout = (SRC / "layout.html").read_text(encoding="utf-8")
    h = site["hours"]
    base = site["siteUrl"].rstrip("/")
    indexable = bool(site.get("indexable"))
    files = {}

    for out_path, tpl, nav_label, title, desc in PAGES:
        root = "../" * out_path.count("/")
        hero = find_photo("hero")
        about = find_photo("about")
        about_alt = "A plated dish at The Blue Heron"

        values = {
            "root": root,
            "site_name": e(site["name"]),
            "tagline": e(site["tagline"]),
            "phone": e(site["phone"]),
            "phone_digits": e(site["phoneDigits"]),
            "email": e(site["email"]),
            "street": e(site["street"]),
            "city": e(site["city"]),
            "region": e(site["region"]),
            "zip": e(site["zip"]),
            "location_note": e(site["locationNote"]),
            "directions_url": e(site["directionsUrl"]),
            "hours_days": e(h["days"]),
            "hours_opens": e(h["opens"]),
            "hours_last": e(h["lastSeating"]),
            "hours_closed": e(h["closedDays"]),
            "reservation_note": e(site["reservationNote"]),
            "dress_note": e(site["dressNote"]),
            "animal_note": e(site["serviceAnimalNote"]),
            "google_reviews_url": e(site["googleReviewsUrl"]),
            "yelp_url": e(site["yelpUrl"]),
            "reviews_cards": review_cards(reviews),
            "social_cards": social_cards(site["social"]),
            "menu_sections": menu_blocks(menu),
            "cheap_sections": menu_blocks(cheap.get("sections", []), pairings=True),
            "cheap_price": e(cheap.get("price", "")),
            "cheap_dates": e(cheap.get("subtitle", "")),
            "cheap_description": e(cheap.get("description", "")),
            "drive_rows": drive_rows(visitors),
            "hours_location": hours_location(site),
            "hero_style": f"background-image:url('{root}{hero}')" if hero else "",
            "about_image": (f'<div><img src="{root}{about}" alt="{about_alt}"></div>' if about else ""),
            "about_class": "" if about else "single",
        }
        content = fill((SRC / "pages" / f"{tpl}.html").read_text(encoding="utf-8"), values, f"src/pages/{tpl}.html")

        nav = []
        for p_out, p_tpl, label, _, _ in PAGES:
            if label:
                cur = ' aria-current="page"' if p_tpl == tpl else ""
                nav.append(f'<a href="{root}{p_out.replace("index.html", "")}"{cur}>{e(label)}</a>')

        url = base + "/" + out_path.replace("index.html", "")
        schema = ""
        if tpl == "home":
            schema = ld_tag(restaurant_schema(site))
        elif tpl == "menu":
            schema = ld_tag(menu_schema(menu, site))
        og = find_photo("og")
        page_values = {
            "title": e(title),
            "description": e(desc),
            "robots_tag": "" if indexable else '<meta name="robots" content="noindex, nofollow">',
            "canonical_tag": f'<link rel="canonical" href="{e(url)}">' if indexable else "",
            "og_image_tag": f'<meta property="og:image" content="{e(base + "/" + og)}">' if og else "",
            "site_name": e(site["name"]),
            "root": root,
            "schema": schema,
            "draft_banner": "" if indexable else '<div class="draft">Draft site. Not public yet and hidden from search engines.</div>',
            "nav": "\n      ".join(nav),
            "content": content,
            "year": str(date.today().year),
            "street": e(site["street"]), "city": e(site["city"]), "region": e(site["region"]),
            "zip": e(site["zip"]), "phone": e(site["phone"]), "phone_digits": e(site["phoneDigits"]),
        }
        files[out_path] = fill(layout, page_values, "src/layout.html")

    if indexable:
        urls = "".join(f"  <url><loc>{e(base + '/' + p[0].replace('index.html', ''))}</loc></url>\n" for p in PAGES)
        files["sitemap.xml"] = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n'
        files["robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"
    else:
        files["robots.txt"] = "User-agent: *\nDisallow: /\n"
    return files


def main():
    check = "--check" in sys.argv
    stale = []
    for rel, text in build().items():
        path = OUT / rel
        old = path.read_text(encoding="utf-8") if path.exists() else None
        if old != text:
            stale.append(rel)
            if not check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
    if check and stale:
        print("docs/ is out of date. Run: python3 scripts/build.py")
        for s in stale:
            print("  ", s)
        sys.exit(1)
    print(("Updated: " + ", ".join(stale)) if stale else "Already up to date.")


if __name__ == "__main__":
    main()
