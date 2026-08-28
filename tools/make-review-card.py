#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Φτιάχνει το εκτυπώσιμο φύλλο με τις κάρτες σχολίου (QR).

Αλλάξτε το URL παρακάτω και τρέξτε ξανά:  python3 tools/make-review-card.py
Απαιτεί: pip install segno
"""
import io
import os
import re

import segno

# --- Πού οδηγεί ο κωδικός QR ------------------------------------------------
URL = "https://dskiad.github.io/entclinic-website/#reviews"
SHOWN = "dskiad.github.io/entclinic-website"
# Όταν ο ιστότοπος μεταφερθεί στο entclinic.gr, βάλτε π.χ.
#   URL   = "https://entclinic.gr/#reviews"
#   SHOWN = "entclinic.gr"
# ---------------------------------------------------------------------------

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "print", "review-card.html")

# Επαναχρησιμοποιούμε το σήμα του ιατρείου που είναι ήδη ενσωματωμένο στη σελίδα
site = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
m = re.search(r'<img src="(data:image/png;base64,[A-Za-z0-9+/=]+)" alt="Λογότυπο', site)
logo = m.group(1) if m else ""
logo_tag = '<img class="logo" src="' + logo + '" alt="">' if logo else ""

# error="q" (25% ανοχή) κρατά τον κωδικό στην έκδοση 5: λιγότερα και μεγαλύτερα
# τετραγωνάκια από το "h", άρα σαρώνεται ευκολότερα στα 24 mm της κάρτας.
qr = segno.make(URL, error="q")
qr_svg = qr.svg_inline(dark="#2E1D12", light=None, border=0)

# Το segno δεν εκδίδει viewBox, οπότε το SVG δεν κλιμακώνεται με CSS: το προσθέτουμε.
_m = re.search(r'<svg width="(\d+)" height="(\d+)"', qr_svg)
if _m:
    qr_svg = qr_svg.replace(
        _m.group(0),
        '<svg viewBox="0 0 %s %s" width="100%%" height="100%%" preserveAspectRatio="xMidYMid meet"'
        % (_m.group(1), _m.group(2)),
        1,
    )

CARD = """    <div class="card">
      <div class="card-in">
        <div class="left">
          __LOGO__
          <div class="head">
            <strong>Λ. Μαριόλης, MD, MSc</strong>
            <span>Ωτορινολαρυγγολόγος</span>
          </div>
          <p class="ask">Η γνώμη σας<br><em>μετράει.</em></p>
          <p class="sub">Αν μείνατε ευχαριστημένοι από την επίσκεψή σας, αφιερώστε
          ένα λεπτό για ένα σύντομο σχόλιο.</p>
          <p class="url">__SHOWN__</p>
        </div>
        <div class="right">
          <div class="qr">__QR__</div>
          <span class="scan">Σαρώστε με<br>την κάμερα</span>
        </div>
      </div>
    </div>
"""

PAGE = """<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Κάρτες σχολίου — ENT Clinic</title>
<style>
  @font-face{font-family:"Inter";src:url("../assets/fonts/Inter-subset.woff2") format("woff2");
    font-weight:100 900;font-style:normal;font-display:swap;}
  @font-face{font-family:"Petrona";src:url("../assets/fonts/Petrona-subset.woff2") format("woff2");
    font-weight:100 900;font-style:normal;font-display:swap;}
  :root{
    --ink:#2E1D12; --ink-soft:#5A4433; --paper:#FAF8F3;
    --brass:#A47C4C; --brass-deep:#7A5626;
    --serif:"Petrona","Noto Serif",Georgia,serif;
    --sans:"Inter","Segoe UI",Arial,sans-serif;
  }
  *{box-sizing:border-box;}
  body{margin:0;background:#EDE7DC;font-family:var(--sans);color:var(--ink);}
  .toolbar{
    max-width:210mm;margin:0 auto;padding:18px 10mm;display:flex;gap:14px;
    align-items:center;justify-content:space-between;flex-wrap:wrap;
  }
  .toolbar p{margin:0;font-size:13px;color:var(--ink-soft);line-height:1.55;max-width:62ch;}
  .toolbar button{
    font-family:var(--sans);font-size:12px;font-weight:700;letter-spacing:.08em;
    text-transform:uppercase;padding:12px 22px;border:1px solid var(--ink);
    background:var(--ink);color:var(--paper);border-radius:2px;cursor:pointer;
  }
  .sheet{
    width:210mm;margin:0 auto 24px;background:#fff;padding:12mm 10mm;
    display:grid;grid-template-columns:repeat(2,1fr);grid-auto-rows:54mm;gap:4mm;
    box-shadow:0 10px 30px rgba(0,0,0,0.12);
  }
  .card{border:1px dashed #C9BCA4;}
  .card-in{
    height:100%;background:var(--paper);display:grid;grid-template-columns:1fr 27mm;
    gap:3mm;padding:4.5mm 4.5mm 4mm;border-left:2.2mm solid var(--brass);
  }
  .left{display:flex;flex-direction:column;min-width:0;}
  .logo{width:7.5mm;height:auto;display:block;margin-bottom:1.2mm;}
  .head strong{display:block;font-family:var(--serif);font-size:9.4pt;font-weight:600;line-height:1.15;}
  .head span{display:block;font-size:5.4pt;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-soft);margin-top:.5mm;}
  .ask{font-family:var(--serif);font-size:12pt;line-height:1.14;margin:2.4mm 0 1.3mm;font-weight:600;}
  .ask em{font-style:italic;color:var(--brass-deep);}
  .sub{font-size:6.4pt;line-height:1.45;color:var(--ink-soft);margin:0;}
  .url{margin:auto 0 0;font-size:5.9pt;font-weight:600;letter-spacing:.02em;color:var(--brass-deep);word-break:break-all;}
  .right{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:1.3mm;}
  .qr{width:24mm;height:24mm;flex:none;}
  .qr svg{width:100%;height:100%;display:block;}
  .scan{font-size:5pt;letter-spacing:.07em;text-transform:uppercase;color:var(--ink-soft);text-align:center;line-height:1.35;}

  @media print{
    body{background:#fff;}
    .toolbar{display:none;}
    .sheet{width:auto;margin:0;box-shadow:none;padding:0;}
    .card{border:1px dashed #D8CDB8;break-inside:avoid;}
    @page{size:A4;margin:12mm 10mm;}
  }
</style>
</head>
<body>
  <div class="toolbar">
    <p><strong>8 κάρτες ανά σελίδα A4</strong>, σε μέγεθος επαγγελματικής κάρτας (85&times;54 mm).
    Τυπώστε σε χαρτόνι 250&ndash;300 g και κόψτε στις διακεκομμένες γραμμές.
    Ο κωδικός QR οδηγεί απευθείας στη φόρμα σχολίων.</p>
    <button onclick="window.print()">Εκτύπωση</button>
  </div>
  <div class="sheet">
__CARDS__  </div>
</body>
</html>
"""

card = CARD.replace("__LOGO__", logo_tag).replace("__SHOWN__", SHOWN).replace("__QR__", qr_svg)
io.open(OUT, "w", encoding="utf-8").write(PAGE.replace("__CARDS__", card * 8))

print("γράφτηκε:", OUT)
print("QR version:", qr.version, "| σήμα:", bool(logo), "| στόχος:", URL)
