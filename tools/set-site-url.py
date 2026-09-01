#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Αλλάζει σε ΟΛΑ τα αρχεία τη διεύθυνση στην οποία ζει ο ιστότοπος.

Οι πλατφόρμες κοινοποίησης (Facebook, Viber, WhatsApp), η Google και ο κωδικός
QR δεν δέχονται σχετικά μονοπάτια: χρειάζονται απόλυτες διευθύνσεις. Αυτές είναι
σκορπισμένες σε πέντε αρχεία, οπότε μια μετακόμιση σε νέο domain τα θέλει όλα
μαζί — αλλιώς η προεπισκόπηση του συνδέσμου και το QR δείχνουν στο παλιό.

  python3 tools/set-site-url.py https://entclinic.gr
  python3 tools/set-site-url.py https://new.entclinic.gr --cname
  python3 tools/set-site-url.py --show

Το --cname γράφει και το αρχείο CNAME που ζητά το GitHub Pages για custom domain.

Ξεχωριστά, το --booking ορίζει πού ζει η κράτηση ραντεβού. Ενημερώνει μαζί τα
κουμπιά «Κλείστε Ραντεβού» και τη σελίδα-δίχτυ book-appointment/index.html, που
πιάνει τους παλιούς συνδέσμους:

  python3 tools/set-site-url.py --booking https://book.entclinic.gr/
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOUCH = ["index.html", "robots.txt", "sitemap.xml", "tools/make-review-card.py"]
# Κάθε απόλυτη διεύθυνση του ιστότοπου, όπου κι αν βρίσκεται.
PAT = re.compile(r"https://(?:[A-Za-z0-9-]+\.)*(?:github\.io|entclinic\.gr)"
                 r"(?:/entclinic-website)?")


def current():
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r'<link rel="canonical" href="([^"]+?)/?"', s)
    return m.group(1) if m else None


CTA_OLD = "https://entclinic.gr/book-appointment/"


def set_booking(url):
    """Δείχνει τα κουμπιά ραντεβού και τη σελίδα-δίχτυ στη νέα διεύθυνση."""
    url = url.rstrip()
    n = 0

    # Κάθε αναφορά, όχι μόνο τα href: η JS μεταβλητή BOOK_URL κάνει την
    # πραγματική ανακατεύθυνση αφού εμφανιστεί το μήνυμα επιβεβαίωσης.
    p = os.path.join(ROOT, "index.html")
    s = old = io.open(p, encoding="utf-8").read()
    s, n = re.subn(r"https?://[^\"'\s>]*book-appointment[^\"'\s>]*", url, s)
    if s != old:
        io.open(p, "w", encoding="utf-8").write(s)
    print("index.html                     %d αναφορές ραντεβού" % n)

    # Η σελίδα-δίχτυ κρατά πάντα τον ΤΕΛΙΚΟ προορισμό, ποτέ τον εαυτό της.
    p = os.path.join(ROOT, "book-appointment", "index.html")
    s = old = io.open(p, encoding="utf-8").read()
    target = "" if url.rstrip("/").endswith("/book-appointment") else url
    s, k = re.subn(r'^const BOOKING_URL = "[^"]*";',
                   'const BOOKING_URL = "%s";' % target, s, count=1, flags=re.M)
    if not k:
        print("ΣΦΑΛΜΑ: δεν βρέθηκε η δήλωση BOOKING_URL.", file=sys.stderr)
        return 1
    if s != old:
        io.open(p, "w", encoding="utf-8").write(s)
    print("book-appointment/index.html    %s"
          % (target or "(κενό: δείχνει τηλέφωνο, δεν ανακατευθύνει)"))
    return 0


def main():
    args = [a for a in sys.argv[1:]]
    if "--booking" in args:
        i = args.index("--booking")
        if i + 1 >= len(args):
            print("Το --booking θέλει διεύθυνση.", file=sys.stderr)
            return 1
        return set_booking(args[i + 1])
    if "--show" in args or not args:
        print("τρέχουσα διεύθυνση:", current())
        found = {}
        for f in TOUCH:
            s = io.open(os.path.join(ROOT, f), encoding="utf-8").read()
            for u in PAT.findall(s):
                found[u] = found.get(u, 0) + 1
        for u, n in sorted(found.items()):
            print("  %-52s %d" % (u, n))
        b = io.open(os.path.join(ROOT, "book-appointment", "index.html"),
                    encoding="utf-8").read()
        m = re.search(r'^const BOOKING_URL = "([^"]*)";', b, re.M)
        cta = re.findall(r'href="([^"]*book-appointment[^"]*)"',
                         io.open(os.path.join(ROOT, "index.html"),
                                 encoding="utf-8").read())
        print("κουμπιά ραντεβού:", sorted(set(cta)) or "-")
        print("σελίδα-δίχτυ δείχνει σε:", (m.group(1) if m else "?") or "(κενό)")
        return 0

    base = args[0].rstrip("/")
    if not base.startswith("https://"):
        print("Η διεύθυνση πρέπει να ξεκινά με https:// — το GitHub Pages σερβίρει "
              "πάντα κρυπτογραφημένα.", file=sys.stderr)
        return 1

    # Ο σύνδεσμος κράτησης ραντεβού ΔΕΝ είναι διεύθυνση του ιστότοπου: δείχνει σε
    # χωριστή υπηρεσία και δεν πρέπει να ξαναγραφτεί.
    KEEP = "https://entclinic.gr/book-appointment/"
    MARK = "\x00KEEP\x00"

    total = 0
    for f in TOUCH:
        p = os.path.join(ROOT, f)
        s = old = io.open(p, encoding="utf-8").read()
        s = s.replace(KEEP, MARK)
        s, n = PAT.subn(base, s)
        s = s.replace(MARK, KEEP)
        if s != old:
            io.open(p, "w", encoding="utf-8").write(s)
        total += n
        print("%-30s %d αντικαταστάσεις" % (f, n))

    host = base.split("//", 1)[1]
    cname = os.path.join(ROOT, "CNAME")
    if "--cname" in args:
        io.open(cname, "w", encoding="utf-8").write(host + "\n")
        print("CNAME                          %s" % host)
    elif os.path.exists(cname):
        print("ΠΡΟΣΟΧΗ: υπάρχει CNAME με '%s' — δώστε --cname για να ενημερωθεί."
              % io.open(cname, encoding="utf-8").read().strip())

    print("\nΣύνολο: %d. Ξαναφτιάξτε τις κάρτες QR:  python3 tools/make-review-card.py"
          % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
