# Balkonien

Das Lexikon meiner Balkon-Pflanzen.

→ **[Online-Version öffnen](https://burmeister12439-futur2.github.io/balkonien/)**

Eine wachsende Sammlung von Pflanzen, die auf meinem Berliner Balkon zu Gast sind oder waren. Mit Steckbrief, Pflegehinweisen und Bildern. Alphabetisch geordnet, durchsuchbar und filterbar.

## Aufbau

- `plants.json` — die Datenquelle. Wer mitarbeiten will: Eintrag anhängen, alphabetisch wird automatisch sortiert.
- `build.py` — Generator (Python 3, keine Abhängigkeiten). `python3 build.py` erzeugt die nächste Version und aktualisiert `index.html`.
- `Bilder/` — eigene Fotos.
- `index.html` — die aktuelle Version (von GitHub Pages serviert).
- `Balkonien_v{N}.html` — Versionsarchiv.

Klaus Burmeister
