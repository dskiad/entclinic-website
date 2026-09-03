#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Φτιάχνει σελίδες ανακατεύθυνσης για τους παλιούς συνδέσμους.

  python3 tools/make-redirects.py            # γράφει ό,τι λέει το docs/redirects.txt
  python3 tools/make-redirects.py --list     # δείχνει τι θα γράψει, χωρίς να γράψει

Το GitHub Pages δεν κάνει 301: δεν υπάρχει .htaccess ούτε ρυθμίσεις server.
Ο μόνος τρόπος να μη σπάσει ένας παλιός σύνδεσμος είναι να υπάρχει αρχείο σε
εκείνο ακριβώς το μονοπάτι. Αυτό το εργαλείο φτιάχνει ένα τέτοιο αρχείο για
κάθε γραμμή του docs/redirects.txt.

Η σελίδα που παράγεται κάνει τρία πράγματα μαζί, γιατί το καθένα πιάνει
διαφορετική περίπτωση:

  meta refresh   δουλεύει και χωρίς JavaScript, και η Google το διαβάζει ως
                 ανακατεύθυνση όταν ο χρόνος είναι 0
  location.replace  δεν αφήνει την ενδιάμεση σελίδα στο ιστορικό, ώστε το
                 «πίσω» του browser να μη γυρίζει σε βρόχο
  rel=canonical  μεταφέρει στη νέα διεύθυνση την αξία που έχει μαζέψει η παλιά

Και αν όλα αποτύχουν, ο επισκέπτης βλέπει έναν ορατό σύνδεσμο και το τηλέφωνο
του ιατρείου — ποτέ λευκή σελίδα.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, "docs", "redirects.txt")
PHONE_TEXT = "211 418 27 37"
PHONE_HREF = "2114182737"

# Φάκελοι με δική τους σελίδα: το εργαλείο δεν τους ακουμπά ποτέ.
PROTECTED = {"assets", "tools", "docs", "print", "book-appointment",
             "korydallos", "nikaia", "peiraias", "peristeri"}


def site_base():
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r'<link rel="canonical" href="([^"]+?)/?"', s)
    return (m.group(1) if m else "https://entclinic.gr").rstrip("/")


def read_map():
    """Επιστρέφει [(μονοπάτι, προορισμός)] από το docs/redirects.txt."""
    if not os.path.exists(MAP):
        return []
    rows = []
    for i, line in enumerate(io.open(MAP, encoding="utf-8"), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            print("γραμμή %d: θέλει ακριβώς δύο στήλες — αγνοήθηκε" % i,
                  file=sys.stderr)
            continue
        old, new = parts
        rows.append((old.strip("/"), new))
    return rows


PAGE = """<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Η σελίδα μετακόμισε — Λ. Μαριόλης, ΩΡΛ</title>
<meta http-equiv="refresh" content="0; url={target}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{up}assets/favicon.ico" sizes="any">
<meta name="theme-color" content="#2E1D12">
<link rel="stylesheet" href="{up}assets/legal.css">
<style>main{{padding:80px 0;}}
  .cta{{display:inline-block;margin-top:22px;padding:15px 28px;background:var(--ink);
    color:var(--paper);text-decoration:none;border-radius:2px;font-size:12.5px;
    font-weight:700;letter-spacing:.1em;text-transform:uppercase;}}
  .cta:hover{{background:var(--brass-deep);color:var(--paper);}}</style>
</head>
<body>

<header class="legal">
  <div class="wrap">
    <div>
      <strong>Λ. Μαριόλης, MD, MSc</strong>
      <span>Ωτορινολαρυγγολογικό Ιατρείο (ΩΡΛ) · Κορυδαλλός</span>
    </div>
    <a href="{up}">← Αρχική σελίδα</a>
  </div>
</header>

<main>
  <div class="wrap">
    <h1>Η σελίδα μετακόμισε</h1>
    <p>Σας μεταφέρουμε αυτόματα. Αν δεν γίνει τίποτα σε δύο δευτερόλεπτα,
    πατήστε τον σύνδεσμο.</p>
    <a class="cta" href="{target}">Συνεχίστε</a>
    <p style="margin-top:30px;">Ή καλέστε μας στο
    <a href="tel:{phone_href}">{phone}</a>.</p>
  </div>
</main>

<script>location.replace({target_js});</script>

</body>
</html>
"""


def build(old, new, base):
    depth = len([p for p in old.split("/") if p])
    up = "../" * depth if depth else "./"
    # Σχετικός προορισμός σημαίνει «μέσα στον ίδιο ιστότοπο»: τον κάνουμε
    # απόλυτο, αλλιώς το canonical δεν έχει νόημα για τη Google.
    target = new if "://" in new else base + "/" + new.lstrip("/")
    return PAGE.format(target=target.replace('"', "&quot;"),
                       canonical=target.split("#")[0],
                       target_js="'%s'" % target.replace("'", "\\'"),
                       up=up, phone=PHONE_TEXT, phone_href=PHONE_HREF)


def main():
    rows = read_map()
    if not rows:
        print("Το docs/redirects.txt δεν έχει ακόμη καμία γραμμή.\n"
              "Προσθέστε τις παλιές διευθύνσεις και ξανατρέξτε.")
        return 0
    base = site_base()
    dry = "--list" in sys.argv[1:]
    for old, new in rows:
        top = old.split("/")[0]
        if top in PROTECTED or not old:
            print("ΠΑΡΑΛΕΙΨΗ %-28s (υπάρχει δική του σελίδα)" % ("/" + old))
            continue
        d = os.path.join(ROOT, *old.split("/"))
        print("%-30s → %s" % ("/" + old + "/", new))
        if dry:
            continue
        if not os.path.isdir(d):
            os.makedirs(d)
        io.open(os.path.join(d, "index.html"), "w",
                encoding="utf-8").write(build(old, new, base))
    if dry:
        print("\n(--list: δεν γράφτηκε τίποτα)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
