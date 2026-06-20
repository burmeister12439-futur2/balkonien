#!/usr/bin/env python3
"""
Balkonien Build-Script
======================
Erzeugt aus plants.json eine fertige HTML-Datei Balkonien_v{N}.html.

Benutzung:
  python build.py                  # autom. Version (höchste vorhandene + 1)
  python build.py --version 5      # explizit v5
  python build.py --validate       # nur Datenprüfung, kein Build

Dieses Skript liest plants.json im selben Ordner und schreibt
Balkonien_v{N}.html in denselben Ordner.
"""
from __future__ import annotations
import argparse, base64, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "plants.json"
SLIDESHOW_DIR = ROOT / "Balkonbilder"

def scan_slideshow() -> list[str]:
    """Sammelt Bild-Dateinamen aus Balkonbilder/, alphabetisch sortiert (= bei iPhones chronologisch)."""
    if not SLIDESHOW_DIR.is_dir():
        return []
    exts = (".jpg",".jpeg",".png",".webp")
    return sorted([p.name for p in SLIDESHOW_DIR.iterdir()
                   if p.suffix.lower() in exts and not p.name.startswith(".")])

REQUIRED = ["id","name","wiss","familie","wikiTitle","emoji",
            "herkunft","lebensdauer","hoehe","bluete","sonne",
            "wasser","pflanzzeit","typ","desc","care","badges","links"]
# Optionale Felder: localImage, photoCredit, erfahrung
TYPEN = ["Blume","Kraut","Wildkraut","Gras","Nutzpflanze","Strauch","Kletterpflanze"]

def load_plants() -> list[dict]:
    if not DATA.exists():
        sys.exit(f"Fehler: plants.json nicht gefunden in {ROOT}")
    try:
        plants = json.loads(DATA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"plants.json ist kein gültiges JSON: {e}")
    if not isinstance(plants, list):
        sys.exit("plants.json muss eine Liste sein.")
    return plants

def validate(plants: list[dict]) -> list[str]:
    errs = []
    ids = set()
    for i, p in enumerate(plants):
        prefix = f"#{i} ({p.get('name','?')})"
        for k in REQUIRED:
            if k not in p:
                errs.append(f"{prefix}: Feld '{k}' fehlt")
        if p.get("id") in ids:
            errs.append(f"{prefix}: id '{p['id']}' kommt mehrfach vor")
        ids.add(p.get("id"))
        if not isinstance(p.get("badges", []), list):
            errs.append(f"{prefix}: 'badges' muss Liste sein")
        if not isinstance(p.get("links", []), list):
            errs.append(f"{prefix}: 'links' muss Liste sein")
        for l in p.get("links", []):
            if not isinstance(l, dict) or "label" not in l or "url" not in l:
                errs.append(f"{prefix}: Link braucht 'label' und 'url'")
    return errs

def next_version() -> int:
    pat = re.compile(r"Balkonien_v(\d+)\.html$")
    versions = [int(pat.search(p.name).group(1))
                for p in ROOT.glob("Balkonien_v*.html")
                if pat.search(p.name)]
    return max(versions, default=0) + 1

TEMPLATE = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Balkonien — Das Lexikon meiner Balkon-Pflanzen</title>
<style>
  :root {
    --bg:#f6f4ee; --paper:#fffdf7; --ink:#2a2a26; --ink-soft:#5a5a52;
    --green:#4a6b3a; --green-soft:#8fa57f; --green-pale:#e6ede0;
    --accent:#b8714a; --rule:#d8d5cb;
    --shadow:0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(0,0,0,.06);
    --radius:14px;
  }
  * { box-sizing:border-box; }
  html, body { margin:0; padding:0; }
  body { background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
    line-height:1.55; -webkit-font-smoothing:antialiased; }
  .wrap { max-width:1280px; margin:0 auto; padding:40px 24px 80px; }
  header.site { text-align:center; padding:48px 16px 32px;
    border-bottom:1px solid var(--rule); margin-bottom:32px; position:relative; }
  header.site .leaf { display:inline-block; font-size:36px; margin-bottom:12px; filter:hue-rotate(-10deg); }
  header.site h1 { font-family:"Cormorant Garamond","Iowan Old Style",Georgia,serif;
    font-weight:500; font-size:clamp(40px,6vw,64px); letter-spacing:-.01em;
    margin:0 0 8px; color:var(--green); }
  header.site .subtitle { font-family:"Cormorant Garamond",Georgia,serif;
    font-style:italic; font-size:clamp(18px,2.2vw,24px); color:var(--ink-soft); margin:0 0 16px; }
  header.site .intro { max-width:640px; margin:0 auto; color:var(--ink-soft); font-size:15px; }
  .controls { display:flex; flex-wrap:wrap; gap:12px; align-items:center;
    margin-bottom:24px; padding:16px; background:var(--paper);
    border:1px solid var(--rule); border-radius:var(--radius); box-shadow:var(--shadow); }
  .controls input[type=search] { flex:1 1 220px; min-width:220px; padding:10px 14px;
    border:1px solid var(--rule); border-radius:999px; background:#fff;
    font-size:15px; font-family:inherit; color:var(--ink); }
  .controls input[type=search]:focus { outline:2px solid var(--green-soft); outline-offset:1px; }
  .filter-group { display:flex; flex-wrap:wrap; gap:6px; }
  .filter-group .label { font-size:12px; text-transform:uppercase; letter-spacing:.06em;
    color:var(--ink-soft); align-self:center; margin-right:4px; }
  .chip { padding:6px 12px; border:1px solid var(--rule); background:#fff;
    border-radius:999px; font-size:13px; color:var(--ink); cursor:pointer;
    transition:all .15s; font-family:inherit; }
  .chip:hover { background:var(--green-pale); }
  .chip.active { background:var(--green); color:#fff; border-color:var(--green); }
  .stats { margin-bottom:20px; font-size:14px; color:var(--ink-soft); padding-left:4px; }
  .stats strong { color:var(--green); font-weight:600; }
  .totals { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px;
    padding:14px 16px; background:var(--paper); border:1px solid var(--rule);
    border-radius:var(--radius); box-shadow:var(--shadow); align-items:center; }
  .totals .total-main { font-family:"Cormorant Garamond",Georgia,serif; font-size:22px;
    color:var(--green); font-weight:500; padding-right:14px;
    border-right:1px solid var(--rule); margin-right:4px; }
  .totals .total-main strong { font-size:26px; }
  .totals .own-photos { font-family:-apple-system,sans-serif; font-size:13px;
    color:var(--ink-soft); margin-left:10px; font-weight:400; }
  .totals .own-photos strong { font-size:14px; color:var(--accent); }
  .totals .typ-chip { padding:6px 12px; border-radius:999px; border:1px solid var(--rule);
    background:#fff; font-size:13px; color:var(--ink); cursor:pointer;
    display:inline-flex; align-items:center; gap:6px; font-family:inherit;
    transition:all .15s; }
  .totals .typ-chip:hover { background:var(--green-pale); }
  .totals .typ-chip.active { background:var(--green); color:#fff; border-color:var(--green); }
  .totals .typ-chip .icon { font-size:14px; }
  .totals .typ-chip .num { font-weight:600; opacity:.85; }
  .totals .typ-chip.zero { opacity:.4; cursor:default; }
  .totals .typ-chip.zero:hover { background:#fff; }
  .start-btn { background:var(--green); color:#fff; border:none; cursor:pointer;
    font-size:14px; padding:10px 18px; border-radius:999px; font-family:inherit;
    font-weight:500; letter-spacing:.01em; transition:background .15s, transform .1s;
    box-shadow:0 1px 3px rgba(0,0,0,.1); }
  .start-btn:hover { background:#3a5530; }
  .start-btn:active { transform:scale(.97); }
  .start-btn .icon { display:inline-block; margin-right:6px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(320px,1fr)); gap:20px; }
  .card { background:var(--paper); border:1px solid var(--rule); border-radius:var(--radius);
    overflow:hidden; box-shadow:var(--shadow); display:flex; flex-direction:column;
    transition:transform .15s, box-shadow .15s; }
  .card:hover { transform:translateY(-2px); box-shadow:0 4px 8px rgba(0,0,0,.06), 0 12px 32px rgba(0,0,0,.08); }
  .card .image { width:100%; aspect-ratio:4/3;
    background:linear-gradient(135deg, var(--green-pale), #d8e2cc);
    position:relative; overflow:hidden; display:flex; align-items:center; justify-content:center; }
  .card .image img { width:100%; height:100%; object-fit:cover; display:block; }
  .card .image .placeholder { font-family:"Cormorant Garamond",Georgia,serif; font-size:22px; color:var(--green); opacity:.5; padding:0 18px; text-align:center; }
  .card .image .credit { position:absolute; bottom:4px; right:6px; font-size:10px;
    color:#fff; background:rgba(0,0,0,.45); padding:2px 6px; border-radius:4px; text-decoration:none; }
  .card .image .credit.local { background:rgba(74,107,58,.7); }
  .card .body { padding:18px 18px 20px; flex:1; display:flex; flex-direction:column; }
  .card h2 { font-family:"Cormorant Garamond",Georgia,serif; font-weight:500;
    font-size:26px; margin:0 0 2px; color:var(--green); letter-spacing:-.005em; }
  .card .wiss { font-style:italic; color:var(--ink-soft); font-size:14px; margin-bottom:10px; }
  .card .meta { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:14px; }
  .badge { font-size:11px; padding:3px 8px; border-radius:4px; background:var(--green-pale);
    color:var(--green); font-weight:500; letter-spacing:.02em; }
  .badge.warn { background:#f8e6d8; color:var(--accent); }
  .badge.fam { background:#eee9dc; color:var(--ink-soft); font-style:italic; }
  .card table { border-collapse:collapse; width:100%; margin-bottom:14px; font-size:13.5px; }
  .card table td { padding:5px 0; border-bottom:1px dotted var(--rule); vertical-align:top; }
  .card table td:first-child { color:var(--ink-soft); width:38%; padding-right:8px; }
  .card table tr:last-child td { border-bottom:none; }
  .card .desc { font-size:14px; color:var(--ink); margin:0 0 10px; }
  .card .care { font-size:13.5px; color:var(--ink-soft); padding:10px 12px;
    background:var(--green-pale); border-left:3px solid var(--green-soft);
    border-radius:0 6px 6px 0; margin-bottom:12px; }
  .card .care strong { color:var(--green); }
  .card .erfahrung { font-size:13.5px; font-style:italic; color:var(--ink);
    padding:10px 12px; background:#fdf4ec; border-left:3px solid var(--accent);
    border-radius:0 6px 6px 0; margin-bottom:12px; }
  .card .erfahrung strong { font-style:normal; color:var(--accent); margin-right:4px; }
  .card .links { margin-top:auto; display:flex; flex-wrap:wrap; gap:8px 16px;
    padding-top:10px; border-top:1px solid var(--rule); }
  .card .links a { color:var(--green); text-decoration:none; font-size:13px;
    border-bottom:1px solid var(--green-soft); }
  .card .links a:hover { color:var(--accent); border-color:var(--accent); }
  .empty { text-align:center; padding:80px 20px; color:var(--ink-soft); font-style:italic; }
  /* Slideshow */
  .slideshow { margin:0 0 36px; padding:0; }
  .slideshow h2 { font-family:"Cormorant Garamond",Georgia,serif; font-weight:500;
    font-size:30px; color:var(--green); margin:0 0 14px; letter-spacing:-.005em; text-align:center; }
  .slideshow .stage { position:relative; background:#1a1a1a;
    border-radius:var(--radius); overflow:hidden; box-shadow:var(--shadow);
    height:min(540px, 65vh); display:flex; align-items:center; justify-content:center; }
  .slideshow .stage img { max-width:100%; max-height:100%; object-fit:contain;
    display:block; opacity:0; transition:opacity .35s; }
  .slideshow .stage img.shown { opacity:1; }
  .slideshow .nav { position:absolute; top:50%; transform:translateY(-50%);
    width:44px; height:44px; border-radius:50%; border:none; cursor:pointer;
    background:rgba(255,255,255,.85); color:var(--ink); font-size:24px;
    line-height:1; display:flex; align-items:center; justify-content:center;
    font-family:inherit; box-shadow:0 2px 6px rgba(0,0,0,.2);
    opacity:0; transition:opacity .2s, background .15s; }
  .slideshow .stage:hover .nav { opacity:1; }
  .slideshow .nav:hover { background:#fff; }
  .slideshow .nav.prev { left:14px; }
  .slideshow .nav.next { right:14px; }
  .slideshow .counter { position:absolute; bottom:10px; right:14px;
    color:#fff; font-size:12px; background:rgba(0,0,0,.55);
    padding:3px 10px; border-radius:999px; font-variant-numeric:tabular-nums; }
  .slideshow .dots { display:flex; justify-content:center; gap:6px; margin-top:12px; flex-wrap:wrap; }
  .slideshow .dot { width:8px; height:8px; border-radius:50%; border:none;
    background:var(--rule); cursor:pointer; padding:0; transition:all .15s; }
  .slideshow .dot:hover { background:var(--green-soft); }
  .slideshow .dot.active { background:var(--green); transform:scale(1.3); }
  @media (max-width:600px) {
    .slideshow .stage { height:50vh; }
    .slideshow h2 { font-size:24px; }
    .slideshow .nav { opacity:1; width:36px; height:36px; font-size:20px; }
  }
  footer.site { margin-top:80px; padding-top:24px; border-top:1px solid var(--rule);
    text-align:center; color:var(--ink-soft); font-size:13px; }
  footer.site a { color:var(--green); }
  @media (max-width:600px) {
    .wrap { padding:24px 12px 60px; }
    .grid { grid-template-columns:1fr; gap:16px; }
  }
</style>
</head>
<body>
<div class="wrap">

<header class="site">
  <h1>Balkonien</h1>
  <p class="subtitle">Das Lexikon meiner Balkon-Pflanzen</p>
  <p class="intro">Ein Balkon ist kein Garten im Kleinen, sondern ein eigener Lebensraum: begrenzt, wetterabhängig, überraschend. Dieses Lexikon sammelt, was dort wächst, blüht, scheitert, wiederkommt oder verschwindet.</p>
  <p class="intro">Eine wachsende Sammlung meiner Balkon-Pflanzen in Berlin — mit Steckbrief, Pflegehinweisen, Bildern, Suche und Filtern.</p>
</header>

<section class="slideshow" id="slideshow" style="display:none">
  <h2>Impressionen 2026</h2>
  <div class="stage" id="slide-stage">
    <img id="slide-img" alt="">
    <button class="nav prev" id="slide-prev" aria-label="Vorheriges Bild">‹</button>
    <button class="nav next" id="slide-next" aria-label="Nächstes Bild">›</button>
    <div class="counter" id="slide-counter"></div>
  </div>
  <div class="dots" id="slide-dots"></div>
</section>

<div class="controls">
  <button class="start-btn" id="start" title="Zurück zur Startansicht — Suche und Filter leeren"><span class="icon">↺</span>Start</button>
  <input type="search" id="search" placeholder="Pflanze suchen (Name, Familie, Herkunft …)">
  <div class="filter-group" data-group="lebensdauer">
    <span class="label">Dauer:</span>
    <button class="chip" data-filter="einjährig">einjährig</button>
    <button class="chip" data-filter="zweijährig">zweijährig</button>
    <button class="chip" data-filter="mehrjährig">mehrjährig</button>
  </div>
  <div class="filter-group" data-group="sonne">
    <span class="label">Sonne:</span>
    <button class="chip" data-filter="vollsonnig">vollsonnig</button>
    <button class="chip" data-filter="sonnig">sonnig</button>
    <button class="chip" data-filter="halbschattig">halbschattig</button>
  </div>
  <div class="filter-group" data-group="badge">
    <span class="label">Merkmal:</span>
    <button class="chip" data-filter="bienenfreundlich">bienenfreundlich</button>
    <button class="chip" data-filter="essbar">essbar</button>
    <button class="chip" data-filter="giftig">giftig</button>
  </div>
</div>

<div class="stats">
  <span id="count">Lade …</span>
</div>

<div class="totals" id="totals"></div>

<main id="grid" class="grid"></main>

<footer class="site">
  Balkonien · Lexikon v__VERSION__ · __BUILD_DATE__ · Bilder via <a href="https://commons.wikimedia.org/" target="_blank" rel="noopener">Wikimedia Commons</a> · Klaus Burmeister
</footer>

</div>

<script id="plants-data" type="application/json">__PLANTS_JSON__</script>
<script id="slideshow-data" type="application/json">__SLIDESHOW_JSON__</script>
<script>
const plants = JSON.parse(document.getElementById("plants-data").textContent);
const slideshowImages = JSON.parse(document.getElementById("slideshow-data").textContent);

/* === SLIDESHOW === */
(function initSlideshow() {
  if (!slideshowImages.length) return;
  const section = document.getElementById("slideshow");
  const img = document.getElementById("slide-img");
  const stage = document.getElementById("slide-stage");
  const dotsEl = document.getElementById("slide-dots");
  const counterEl = document.getElementById("slide-counter");
  section.style.display = "block";
  let idx = 0;
  const dots = slideshowImages.map((_, i) => {
    const d = document.createElement("button");
    d.className = "dot"; d.setAttribute("aria-label", `Bild ${i+1}`);
    d.addEventListener("click", () => { show(i); restart(); });
    dotsEl.appendChild(d);
    return d;
  });
  function tryLoad(urls, j, onSuccess) {
    if (j >= urls.length) return;
    const probe = new Image();
    probe.onload = () => onSuccess(urls[j]);
    probe.onerror = () => tryLoad(urls, j + 1, onSuccess);
    probe.src = urls[j];
  }
  function show(i) {
    idx = (i + slideshowImages.length) % slideshowImages.length;
    img.classList.remove("shown");
    const file = encodeURIComponent(slideshowImages[idx]);
    // Erst Balkonbilder/ probieren (lokal), dann Root (GitHub)
    tryLoad(["Balkonbilder/" + file, file], 0, src => {
      img.src = src;
      requestAnimationFrame(() => img.classList.add("shown"));
    });
    dots.forEach((d, j) => d.classList.toggle("active", j === idx));
    counterEl.textContent = `${idx+1} / ${slideshowImages.length}`;
  }
  document.getElementById("slide-prev").addEventListener("click", () => { show(idx-1); restart(); });
  document.getElementById("slide-next").addEventListener("click", () => { show(idx+1); restart(); });
  document.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT") return;
    if (e.key === "ArrowLeft") { show(idx-1); restart(); }
    else if (e.key === "ArrowRight") { show(idx+1); restart(); }
  });
  let timer = null;
  function start() { timer = setInterval(() => show(idx+1), 3000); }
  function stop() { clearInterval(timer); }
  function restart() { stop(); start(); }
  stage.addEventListener("mouseenter", stop);
  stage.addEventListener("mouseleave", start);
  show(0); start();
})();


function sonneTags(s) {
  s = (s || "").toLowerCase();
  const tags = [];
  if (s.includes("vollsonnig")) tags.push("vollsonnig","sonnig");
  else if (s.includes("sonnig")) tags.push("sonnig");
  if (s.includes("halbschattig")) tags.push("halbschattig");
  if (s.includes("schattig") && !s.includes("halbschattig")) tags.push("schattig");
  return tags;
}
function lebensdauerTags(l) {
  l = (l || "").toLowerCase();
  const tags = [];
  if (l.includes("einjährig")) tags.push("einjährig");
  if (l.includes("zweijährig")) tags.push("zweijährig");
  if (l.includes("mehrjährig") || l.includes("staude") || l.includes("strauch") || l.includes("kletterpflanze")) tags.push("mehrjährig");
  return tags;
}
function badgeMatch(plant, filter) {
  return (plant.badges || []).some(b => b.toLowerCase().includes(filter.toLowerCase()));
}
const grid = document.getElementById("grid");
const search = document.getElementById("search");
const countEl = document.getElementById("count");
const startBtn = document.getElementById("start");
const totalsEl = document.getElementById("totals");
const filterButtons = document.querySelectorAll(".chip");
let activeFilters = { lebensdauer:null, sonne:null, badge:null, typ:null };

const TYP_ORDER = ["Blume","Kraut","Wildkraut","Gras","Nutzpflanze","Strauch","Kletterpflanze"];

function renderTotals() {
  const counts = {};
  for (const t of TYP_ORDER) counts[t] = 0;
  for (const p of plants) {
    if (counts[p.typ] !== undefined) counts[p.typ]++;
    else counts[p.typ] = 1;
  }
  const chips = TYP_ORDER.map(t => {
    const n = counts[t] || 0;
    const isActive = activeFilters.typ === t;
    const zero = n === 0 ? " zero" : "";
    return `<button class="typ-chip${isActive ? " active" : ""}${zero}" data-typ="${t}"${zero ? " disabled" : ""}>
      ${t}<span class="num">${n}</span>
    </button>`;
  }).join("");
  const eigene = plants.filter(p => p.localImage).length;
  totalsEl.innerHTML = `
    <span class="total-main"><strong>${plants.length}</strong> Pflanzen<span class="own-photos">· <strong>${eigene}</strong> eigene Fotos</span></span>
    ${chips}
  `;
  totalsEl.querySelectorAll(".typ-chip").forEach(btn => {
    if (btn.classList.contains("zero")) return;
    btn.addEventListener("click", () => {
      const t = btn.getAttribute("data-typ");
      activeFilters.typ = (activeFilters.typ === t) ? null : t;
      render();
    });
  });
}

plants.sort((a,b) => a.name.localeCompare(b.name, "de"));

function esc(s) {
  return String(s).replace(/[&<>"']/g, c =>
    ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function renderCard(p) {
  const linksHtml = (p.links || []).map(l =>
    `<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)} ↗</a>`
  ).join("");
  const badgesHtml = (p.badges || []).map(b => {
    const isWarn = /giftig/i.test(b);
    return `<span class="badge ${isWarn ? "warn" : ""}">${esc(b)}</span>`;
  }).join("");
  // Lokales Bild hat Vorrang vor Wikipedia-Auto-Fetch
  const wikiAttr = p.localImage ? "" : esc(p.wikiTitle);
  const imageInner = p.localImage
    ? `<img src="${esc(p.localImage)}" alt="" loading="lazy">${p.photoCredit ? `<span class="credit local">${esc(p.photoCredit)}</span>` : ""}`
    : `<span class="placeholder">${esc(p.name)}</span>`;
  return `
    <article class="card" data-id="${esc(p.id)}">
      <div class="image" data-wiki="${wikiAttr}">
        ${imageInner}
      </div>
      <div class="body">
        <h2>${esc(p.name)}</h2>
        <div class="wiss">${esc(p.wiss)}</div>
        <div class="meta">
          <span class="badge fam">${esc(p.familie)}</span>
          ${badgesHtml}
        </div>
        <table>
          <tr><td>Herkunft</td><td>${esc(p.herkunft)}</td></tr>
          <tr><td>Lebensdauer</td><td>${esc(p.lebensdauer)}</td></tr>
          <tr><td>Wuchshöhe</td><td>${esc(p.hoehe)}</td></tr>
          <tr><td>Blütezeit</td><td>${esc(p.bluete)}</td></tr>
          <tr><td>Sonne</td><td>${esc(p.sonne)}</td></tr>
          <tr><td>Wasser</td><td>${esc(p.wasser)}</td></tr>
          <tr><td>Pflanzzeit</td><td>${esc(p.pflanzzeit)}</td></tr>
        </table>
        <p class="desc">${esc(p.desc)}</p>
        <div class="care"><strong>Pflege:</strong> ${esc(p.care)}</div>
        ${p.erfahrung ? `<div class="erfahrung"><strong>Meine Erfahrung:</strong>${esc(p.erfahrung)}</div>` : ""}
        <div class="links">${linksHtml}</div>
      </div>
    </article>
  `;
}

function matchesFilters(p) {
  const q = search.value.trim().toLowerCase();
  if (q) {
    const hay = [p.name, p.wiss, p.familie, p.herkunft, p.desc].join(" ").toLowerCase();
    if (!hay.includes(q)) return false;
  }
  if (activeFilters.lebensdauer && !lebensdauerTags(p.lebensdauer).includes(activeFilters.lebensdauer)) return false;
  if (activeFilters.sonne && !sonneTags(p.sonne).includes(activeFilters.sonne)) return false;
  if (activeFilters.badge && !badgeMatch(p, activeFilters.badge)) return false;
  if (activeFilters.typ && p.typ !== activeFilters.typ) return false;
  return true;
}

function render() {
  const filtered = plants.filter(matchesFilters);
  grid.innerHTML = filtered.length
    ? filtered.map(renderCard).join("")
    : `<div class="empty">Keine Pflanze passt zu dieser Filterkombination.</div>`;
  countEl.innerHTML = filtered.length === plants.length
    ? `Alle <strong>${plants.length}</strong> Pflanzen sichtbar`
    : `<strong>${filtered.length}</strong> von ${plants.length} Pflanzen sichtbar`;
  renderTotals();
  loadImages();
}

const imgCache = {};
async function loadImages() {
  const imgBoxes = document.querySelectorAll(".image[data-wiki]");
  for (const box of imgBoxes) {
    const title = box.getAttribute("data-wiki");
    if (!title || box.querySelector("img")) continue;
    if (imgCache[title]) { applyImage(box, imgCache[title], title); continue; }
    try {
      const url = `https://de.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(title)}`;
      const r = await fetch(url);
      if (!r.ok) throw new Error("not ok");
      const data = await r.json();
      const thumb = (data.originalimage && data.originalimage.source) || (data.thumbnail && data.thumbnail.source);
      if (thumb) { imgCache[title] = thumb; applyImage(box, thumb, title); }
    } catch (e) { /* Placeholder bleibt */ }
  }
}
function applyImage(box, src, title) {
  if (box.querySelector("img")) return;
  const img = document.createElement("img");
  img.src = src; img.alt = ""; img.loading = "lazy";
  img.onerror = () => img.remove();
  box.appendChild(img);
  const credit = document.createElement("a");
  credit.href = `https://de.wikipedia.org/wiki/${encodeURIComponent(title)}`;
  credit.target = "_blank"; credit.rel = "noopener";
  credit.className = "credit"; credit.textContent = "Wikipedia ↗";
  box.appendChild(credit);
}

search.addEventListener("input", render);
filterButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const group = btn.parentElement.getAttribute("data-group");
    const value = btn.getAttribute("data-filter");
    if (activeFilters[group] === value) {
      activeFilters[group] = null;
      btn.classList.remove("active");
    } else {
      activeFilters[group] = value;
      btn.parentElement.querySelectorAll(".chip").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    }
    render();
  });
});
startBtn.addEventListener("click", () => {
  search.value = "";
  activeFilters = { lebensdauer:null, sonne:null, badge:null, typ:null };
  document.querySelectorAll(".chip.active").forEach(b => b.classList.remove("active"));
  render();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

render();
</script>
</body>
</html>
"""

def build(version: int) -> Path:
    plants = load_plants()
    errs = validate(plants)
    if errs:
        print("⚠️ Validierungsfehler:")
        for e in errs:
            print(" -", e)
        sys.exit(1)
    plants.sort(key=lambda p: p["name"])
    from datetime import date
    build_date = date.today().strftime("%B %Y")
    # Monatsname → DE
    de_months = {"January":"Januar","February":"Februar","March":"März",
                 "April":"April","May":"Mai","June":"Juni","July":"Juli",
                 "August":"August","September":"September","October":"Oktober",
                 "November":"November","December":"Dezember"}
    for en, de in de_months.items():
        build_date = build_date.replace(en, de)
    # JSON in <script type="application/json"> einbetten — eingebauter Schutz
    # gegen </script> Sequenzen in den Daten
    plants_json = json.dumps([{k: v for k, v in p.items() if k != "emoji"} for p in plants], ensure_ascii=False, indent=2)
    plants_json = plants_json.replace("</", "<\\/")
    slideshow = scan_slideshow()
    slideshow_json = json.dumps(slideshow, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__PLANTS_JSON__", plants_json)
    html = html.replace("__SLIDESHOW_JSON__", slideshow_json)
    html = html.replace("__VERSION__", str(version))
    html = html.replace("__BUILD_DATE__", build_date)
    out = ROOT / f"Balkonien_v{version}.html"
    out.write_text(html, encoding="utf-8")
    # index.html spiegelt immer die aktuelle Version — für GitHub Pages
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    if slideshow:
        print(f"  📷 Slideshow: {len(slideshow)} Bilder eingebunden")
    return out

def file_to_data_uri(path: Path) -> str | None:
    if not path.exists():
        return None
    ext = path.suffix.lstrip(".").lower()
    mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","webp":"webp","gif":"gif"}.get(ext)
    if not mime:
        return None
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/{mime};base64,{b64}"

def wiki_to_data_uri(title: str) -> str | None:
    """Holt das Vorschaubild eines deutschen Wikipedia-Artikels und liefert eine Data-URI."""
    if not title:
        return None
    try:
        summary_url = f"https://de.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
        req = urllib.request.Request(summary_url, headers={"User-Agent": "Balkonien-Build/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        thumb_url = (data.get("originalimage", {}).get("source")
                     or data.get("thumbnail", {}).get("source"))
        if not thumb_url:
            return None
        ireq = urllib.request.Request(thumb_url, headers={"User-Agent": "Balkonien-Build/1.0"})
        with urllib.request.urlopen(ireq, timeout=20) as ir:
            img_data = ir.read()
        ext = thumb_url.rsplit(".", 1)[-1].split("?")[0].lower()
        mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","webp":"webp",
                "gif":"gif","svg":"svg+xml"}.get(ext, "jpeg")
        b64 = base64.b64encode(img_data).decode()
        return f"data:image/{mime};base64,{b64}"
    except Exception:
        return None

def build_share(version: int) -> Path:
    """Baut eine selbstgenügsame Version: alle Bilder als Data-URIs eingebettet."""
    plants = load_plants()
    errs = validate(plants)
    if errs:
        print("⚠️ Validierungsfehler:")
        for e in errs: print(" -", e)
        sys.exit(1)
    plants.sort(key=lambda p: p["name"])

    print(f"Bilder einbetten ({len(plants)} Pflanzen)…")
    embedded_local = embedded_wiki = skipped = 0
    for i, p in enumerate(plants, 1):
        if p.get("localImage"):
            uri = file_to_data_uri(ROOT / p["localImage"])
            if uri:
                p["localImage"] = uri
                embedded_local += 1
                print(f"  [{i:2}/{len(plants)}] {p['name']}: lokales Bild ✓")
            else:
                skipped += 1
                print(f"  [{i:2}/{len(plants)}] {p['name']}: lokales Bild fehlt ✗")
        elif p.get("wikiTitle"):
            uri = wiki_to_data_uri(p["wikiTitle"])
            if uri:
                p["localImage"] = uri
                p["wikiTitle"] = ""  # Unterdrückt JS-Fetch in der Share-Version
                embedded_wiki += 1
                print(f"  [{i:2}/{len(plants)}] {p['name']}: Wikipedia-Bild ✓")
            else:
                skipped += 1
                print(f"  [{i:2}/{len(plants)}] {p['name']}: Wikipedia liefert kein Bild ✗")
            time.sleep(0.5)  # Rate-Limit-Schutz
        else:
            skipped += 1
    print(f"\n✓ Eingebettet: {embedded_local} lokale, {embedded_wiki} Wikipedia, {skipped} ohne Bild")

    # Render mit derselben Template-Logik wie build(), aber mit unsigniertem Suffix
    from datetime import date
    build_date = date.today().strftime("%B %Y")
    de_months = {"January":"Januar","February":"Februar","March":"März",
                 "April":"April","May":"Mai","June":"Juni","July":"Juli",
                 "August":"August","September":"September","October":"Oktober",
                 "November":"November","December":"Dezember"}
    for en, de in de_months.items():
        build_date = build_date.replace(en, de)
    plants_json = json.dumps([{k: v for k, v in p.items() if k != "emoji"} for p in plants], ensure_ascii=False, indent=2)
    plants_json = plants_json.replace("</", "<\\/")
    # Share-Version verzichtet auf Slideshow, sonst wird die Datei zu groß
    html = TEMPLATE.replace("__PLANTS_JSON__", plants_json)
    html = html.replace("__SLIDESHOW_JSON__", "[]")
    html = html.replace("__VERSION__", f"{version}-share")
    html = html.replace("__BUILD_DATE__", build_date)
    out = ROOT / f"Balkonien_v{version}_share.html"
    out.write_text(html, encoding="utf-8")
    return out

def main():
    ap = argparse.ArgumentParser(description="Balkonien-Build")
    ap.add_argument("--version", type=int, help="Explizite Version (sonst auto-bump)")
    ap.add_argument("--validate", action="store_true", help="Nur validieren")
    ap.add_argument("--share", action="store_true",
                    help="Selbstgenügsame Datei: alle Bilder als Base64 eingebettet")
    args = ap.parse_args()

    plants = load_plants()
    errs = validate(plants)
    if errs:
        print("⚠️ Validierungsfehler:")
        for e in errs: print(" -", e)
        sys.exit(1)
    print(f"✓ {len(plants)} Pflanzen, plants.json gültig.")
    if args.validate:
        return
    v = args.version or next_version()
    if args.share:
        # Share immer auf höchste vorhandene Version setzen
        if args.version is None:
            v = next_version() - 1 or 1
        out = build_share(v)
    else:
        out = build(v)
    print(f"✓ {out.name} gebaut ({out.stat().st_size} Bytes, ~{out.stat().st_size/1024/1024:.1f} MB)")

if __name__ == "__main__":
    main()
