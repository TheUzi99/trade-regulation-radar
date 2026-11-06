# Trade Regulation Radar

Daily, automated tracking of EU trade law, sanctions and policy changes relevant to Türkiye, the CIS and Central Asia. A non-commercial portfolio project using public sources only.

- `sources.json` — sources, filters and licences. Empty `url` means not configured yet.
- `radar/collect.py` — fetches sources, records new items (feeds) and added/removed/changed records (lists).
- `radar/build_site.py` — builds the site in English, German, Turkish, Russian and French in `site/`.
- `.github/workflows/radar.yml` — runs daily at 05:17 UTC and publishes to GitHub Pages.

Run locally: `python -m unittest discover -s tests && python -m radar.collect . && python -m radar.build_site .`

Not legal advice. Always check the linked official text.
