#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Φτιάχνει ένα .zip με ΜΟΝΟ τα αρχεία που ανεβαίνουν σε server φιλοξενίας.

Ο ιστότοπος είναι εξ ολοκλήρου στατικός: HTML, CSS, γραμματοσειρές και εικόνες.
Δεν χρειάζεται βάση δεδομένων, PHP, WordPress ή διαδικασία build. Τρέχει σε
οποιονδήποτε server, άρα και σε αυτόν που ήδη φιλοξενεί το entclinic.gr.

  python3 tools/make-upload-bundle.py

Ανεβάστε το περιεχόμενο του zip στον φάκελο δημοσίευσης (public_html, httpdocs
ή ό,τι δείχνει το panel σας). Μένουν έξω τα εργαλεία, η τεκμηρίωση, οι κάρτες
QR και το ιστορικό του git — δεν έχουν θέση σε δημόσιο server.
"""
import io
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "dist", "entclinic-website.zip")

FILES = ["index.html", "privacy.html", "terms.html", "404.html",
         "robots.txt", "sitemap.xml"]
DIRS = ["assets", "book-appointment"]
SKIP_EXT = {".woff2.br"}


def main():
    missing = [f for f in FILES if not os.path.exists(os.path.join(ROOT, f))]
    if missing:
        print("Λείπουν αρχεία:", ", ".join(missing), file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n = 0
    total = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in FILES:
            z.write(os.path.join(ROOT, f), f)
            n += 1
            total += os.path.getsize(os.path.join(ROOT, f))
        for d in DIRS:
            for base, _, names in os.walk(os.path.join(ROOT, d)):
                for name in sorted(names):
                    p = os.path.join(base, name)
                    rel = os.path.relpath(p, ROOT)
                    if os.path.splitext(name)[1] in SKIP_EXT:
                        continue
                    z.write(p, rel)
                    n += 1
                    total += os.path.getsize(p)

    print("γράφτηκε: %s" % OUT)
    print("%d αρχεία, %.1f MB ασυμπίεστα, %.1f MB το zip"
          % (n, total / 1e6, os.path.getsize(OUT) / 1e6))

    # Ένας server που δεν είναι το GitHub Pages δεν διαβάζει το CNAME, και μια
    # ξεχασμένη απόλυτη διεύθυνση github.io στέλνει την προεπισκόπηση συνδέσμου
    # και τη Google στο λάθος μέρος.
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    if "github.io" in s:
        print("\nΠΡΟΣΟΧΗ: το index.html περιέχει ακόμη διευθύνσεις github.io.")
        print("Πριν ανεβάσετε:  python3 tools/set-site-url.py https://entclinic.gr")
    return 0


if __name__ == "__main__":
    sys.exit(main())
