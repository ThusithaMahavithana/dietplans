# DietPlans menu catalogue

A buildless, browser-local lunch and dinner library. No framework, package installation, API key or backend is required.

Run from this directory:

```sh
python3 -m http.server 8767 --bind 127.0.0.1
```

Open http://127.0.0.1:8767. Use HTTP rather than opening the HTML directly so JSON loading, installation and offline caching work.

## Structure

- `index.html`, `styles.css`, `app.js`: accessible, responsive catalogue.
- `data/menus.json`: source contents, quantities, provenance, reviews, comparisons and image mappings.
- `data/image-prompts.json`: one regeneration prompt per stable menu ID.
- `assets/meals/`: distinct generated meal images, named by menu ID.
- `reports/extraction.md`: full mention index and duplicate decisions.
- `reports/source-audit.json`: complete source message census and exclusions.
- `scripts/extract.py`: reproducible extraction; only reads `sources/`.
- `scripts/validate.py`: independent coverage and integrity checks.

Rebuild data and validate with `python3 scripts/extract.py` and `python3 scripts/validate.py`. Menu IDs are based on the first heading's original source line, so the same frozen source produces stable IDs. Keep this source snapshot unchanged. Changes to extraction rules require reviewing the report and image mappings.

## Interpretation

First/Second meal are provisional Lunch/Dinner browsing categories, explicitly flagged. Breakfast is excluded. Alternatives are preserved within one menu. Full source excerpts and linked recipes are retained, including ambiguous quantities and ingredient/method conflicts. The catalogue does not republish health readings, medication discussions or personal identifiers.

Nutrition suggestions are editorial and optional. Whole-meal calorie and macro totals are withheld where portion information is insufficient. References are linked in the app.

## Offline

The service worker uses a new cache namespace, removes old `diet-companion-*` caches, and uses network-first delivery for HTML and data. Only app resources are cached; the private source chat is excluded. Meal images are cached when viewed, not all downloaded at installation.

Bookmarks use `dietplans-saved` in localStorage. Legacy app code and icons have been removed.

## Images

Illustrations are AI-generated and are not exact portion guides. They depict a selected source alternative, not all alternatives at once. Source quantities are authoritative; unquantified servings in a picture are illustrative. Prompts include ingredients, sides and preparation. Missing images are explicitly labelled rather than replaced by generic food photographs.

## Checks and review

Run `python3 scripts/validate.py` for data integrity. With Node installed, run `node scripts/check-app.mjs` for app behavior checks. See `reports/validation.md` for completed checks and browser-testing limitations, and `reports/nutrition-review.md` for the nutrition policy and uncertainties.

All 235 meal illustrations are local JPEGs. Optional `scripts/optimize_images.py` uses Pillow only during asset maintenance; the website itself needs no installed packages.
