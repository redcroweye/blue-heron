# The Blue Heron website

Static site for The Blue Heron, Rapid City. HTML, CSS and JSON only.
This is the development copy. The live site is built from a separate repo.

## Update the menu
1. Edit `data/menu.json` (dishes, prices, descriptions).
2. Run `python3 scripts/build.py`
3. Commit the changed files.

## Update the Cheap Date Night menu
Same steps, using `cheap-date-nights/data/cheap-date-menu.json`.

## Update reviews or business details
- Reviews: `data/reviews.json`
- Address, phone, search-engine details: `data/restaurant.json`
Then run `python3 scripts/build.py`.

## See it on your computer
```
python3 scripts/build.py
python3 -m http.server 8000
```
Open http://localhost:8000

If you forget to run the build step, a check on GitHub will flag it.

## Folders
- `data/` the content you edit
- `scripts/` the build step
- `square/` future Square connections
