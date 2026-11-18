# The Blue Heron website 2.0

Plain HTML, CSS and JSON. No frameworks. This is the development copy; the live
site is a separate repo and is not touched by anything here.

## How it works
- `data/` is the content you edit (menu, hours, reviews, phone, links).
- `src/` is the page layout. You rarely need to touch it.
- `docs/` is the finished website that GitHub Pages serves. It is generated.
- `scripts/build.py` turns data + src into docs.

## Update the menu
1. Edit `data/menu.json`.
2. Run `python3 scripts/build.py`.
3. Commit everything that changed (including `docs/`).

## Other common edits
| To change | Edit |
|---|---|
| Hours, phone, email, address, social links | `data/site.json` |
| Cheap Date Night price, dates, dishes | `data/cheap-date.json` |
| Reviews | `data/reviews.json` |
| Drive times on the Visit page | `data/visitors.json` |
| Page wording | files in `src/pages/` |
| Colors and fonts | `docs/assets/css/site.css` (top of file) |

Always run `python3 scripts/build.py` afterward.

## Photos
Drop files into `docs/assets/photos/` with these exact names and the site uses
them automatically after a build:
- `hero.jpg` big banner background
- `about.jpg` photo beside the home page intro
- `og.jpg` image shown when the site is shared on social media

Keep photos under about 400 KB each (resize before uploading).

## See it on your computer
```
python3 scripts/build.py
cd docs
python3 -m http.server 8000
```
Open http://localhost:8000

## Put it on GitHub Pages
Repo Settings, Pages, "Deploy from a branch", branch `main`, folder `/docs`.

## Going live later
While `"indexable": false` in `data/site.json`, every page tells search engines
to stay away and shows a "Draft site" banner. That keeps this copy from
competing with the live site. When you switch over: set `"indexable": true`,
confirm `siteUrl`, add the closing time to `hours.schemaCloses` (for example
`"21:00"` format is 24 hour), rebuild, and publish.

## Before launch checklist
- Cheap Date Night dates in `data/cheap-date.json` are old. Update them.
- Confirm drive times in `data/visitors.json`.
- Add photos.
- Decide how reservations work (phone and email only right now).
- Private events is an email link; there is no form yet.

## Square
Future Square connections go in `square/`. Never put access tokens in this repo.
