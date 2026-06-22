# Balkonien — Projekt-Cockpit

**Ort (Master):** `/Users/kburmeister/Documents/home/Klaus_nc/Balkonien`
**Art:** Persönliches Projekt — Lexikon der Balkon-Pflanzen + Foto-Slideshow, als statische Website (GitHub Pages).
**Online:** https://burmeister12439-futur2.github.io/balkonien/
**Stand:** 20. Juni 2026 — **v17**

## Worum es geht

„Balkonien" ist eine generierte Website mit zwei Teilen: einem durchsuch- und
filterbaren Lexikon der Balkon-Pflanzen und der Foto-Slideshow „Impressionen 2026".
Die Seite entsteht aus einer Datenquelle und einem Generator — nicht von Hand.

## So funktioniert das Projekt

| Datei / Ordner | Zweck |
|----------------|-------|
| `plants.json` | Datenquelle aller Pflanzen-Steckbriefe. Neue Pflanze = Eintrag anhängen, wird automatisch alphabetisch einsortiert. |
| `build.py` | Generator (Python 3, ohne Abhängigkeiten). `python3 build.py --version N` erzeugt `Balkonien_vN.html` und aktualisiert `index.html`. |
| `index.html` | Die aktuelle Version — genau das, was GitHub Pages ausliefert. |
| `Balkonien_v{N}.html` | Versionsarchiv (eine Datei je Version). |
| `Balkonbilder/` | Fotos für die Slideshow. Dateiname bestimmt die Reihenfolge (alphabetisch = bei iPhone-Fotos chronologisch). |
| `Bilder/` | Einzelne Pflanzen-Bilder (z. B. wo es kein Wikipedia-Foto gibt). |
| `README.md` | Öffentliche Kurzbeschreibung im Repo. |

## Aktueller Inhalt (v15)

- **44 Pflanzen** im Lexikon.
- **23 Fotos** in der Slideshow.

## Was am 20.06.2026 geschah

- Fünf neue Pflanzen ergänzt: Echtes Johanniskraut, Strand-Grasnelke, Echter Lavendel, Petunie, Große Sterndolde (38 → 43).
- Acht neue Balkonfotos in die Slideshow übernommen: IMG_9186, 9191, 9346, 9355, 9599, 9601, 9620, 9626 (15 → 23).
- Das Master-Projekt aus `Documents/GitHub/balkonien` in diesen Ordner zusammengeführt (inkl. Git-Historie). `GitHub/balkonien` bleibt als unveränderte Sicherung bestehen.
- v15 gebaut (`index.html` + `Balkonien_v15.html`), committet und gepusht.
- v16: alle Emoji-Symbole von der Website entfernt (Kopf-Blatt, Typ-Icons, Sonne/Wasser-Symbole, Karten-Platzhalter zeigt jetzt den Pflanzennamen). `build.py` entsprechend angepasst; Emoji bleibt nur als (unsichtbares) Pflichtfeld in `plants.json`, wird aber nicht mehr ins HTML eingebettet.
- Versehentlich zuvor in diesem Ordner erzeugte Dateien liegen unter `_Archiv_Fehlversuch_20260620/` und sind per `.gitignore` ausgenommen.

## Nächste Schritte / offen

- **Veröffentlichen:** v15 ist nur lokal gebaut. Zum Online-Stellen die Änderungen committen und zu GitHub pushen (z. B. via GitHub Desktop). Die Online-Seite steht bis dahin auf v14.
- Bei weiteren Pflanzen: Eintrag in `plants.json`, dann `python3 build.py --version 17`.
- Weitere Balkonfotos einfach in `Balkonbilder/` legen und neu bauen.

## Versionshistorie

- **v17** (20.06.2026): Wegwarte (Cichorium intybus) ergänzt — 44 Pflanzen.
- **v16** (20.06.2026): Alle Emoji-Symbole von der Website entfernt.
- **v15** (20.06.2026): +5 Pflanzen (43 gesamt), +8 Fotos (23 gesamt); Projekt in `Klaus_nc/Balkonien` als Master zusammengeführt.
- **v14** (Mai 2026): 38 Pflanzen, Slideshow „Impressionen 2026", neuer Look.
