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
FIXED = ["robots.txt", "sitemap.xml", "tools/make-review-card.py"]


def pages():
    """Οι σελίδες που κρατούν κουμπί ραντεβού: η αρχική και οι περιοχές.

    Ανακαλύπτονται, δεν απαριθμούνται: όποια σελίδα περιοχής προστεθεί αργότερα
    ακολουθεί μόνη της τη μετακόμιση σε νέο domain. Η σελίδα-δίχτυ εξαιρείται —
    την ενημερώνει χωριστά η set_booking, με τον ΤΕΛΙΚΟ προορισμό.
    """
    out = ["index.html"]
    for d in sorted(os.listdir(ROOT)):
        if d in ("book-appointment", "assets", "tools", "docs", "print"):
            continue
        if os.path.isfile(os.path.join(ROOT, d, "index.html")):
            out.append("%s/index.html" % d)
    return out


TOUCH = pages() + FIXED
# Κάθε απόλυτη διεύθυνση του ιστότοπου, όπου κι αν βρίσκεται.
PAT = re.compile(r"https://(?:[A-Za-z0-9-]+\.)*(?:github\.io|entclinic\.gr)"
                 r"(?:/entclinic-website)?")


def current():
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r'<link rel="canonical" href="([^"]+?)/?"', s)
    return m.group(1) if m else None


CTA_OLD = "https://entclinic.gr/book-appointment/"


def booking():
    """Η τρέχουσα διεύθυνση κράτησης, όπως τη δείχνουν τα κουμπιά."""
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r"https?://[^\"'\s>]*book-appointment[^\"'\s>]*", s)
    return m.group(0) if m else CTA_OLD


def set_booking(url):
    """Δείχνει τα κουμπιά ραντεβού και τη σελίδα-δίχτυ στη νέα διεύθυνση."""
    url = url.rstrip()
    n = 0

    # Κάθε αναφορά, όχι μόνο τα href: η JS μεταβλητή BOOK_URL κάνει την
    # πραγματική ανακατεύθυνση αφού εμφανιστεί το μήνυμα επιβεβαίωσης. Τα
    # κουμπιά των σελίδων περιοχής θέλουν την ίδια διεύθυνση.
    for f in pages():
        p = os.path.join(ROOT, f)
        s = old = io.open(p, encoding="utf-8").read()
        s, k = re.subn(r"https?://[^\"'\s>]*book-appointment[^\"'\s>]*", url, s)
        if s != old:
            io.open(p, "w", encoding="utf-8").write(s)
        n += k
        print("%-30s %d αναφορές ραντεβού" % (f, k))

    # Η σελίδα-δίχτυ κρατά πάντα τον ΤΕΛΙΚΟ προορισμό, ποτέ τον εαυτό της.
    p = os.path.join(ROOT, "book-appointment", "index.html")
    s = old = io.open(p, encoding="utf-8").read()
    # Ο έλεγχος γίνεται με ΟΛΟΚΛΗΡΗ τη διεύθυνση, όχι μόνο με το μονοπάτι: το
    # booking.entclinic.gr/book-appointment/ είναι άλλος host, άρα νόμιμος
    # προορισμός. Μόνο η ίδια η σελίδα-δίχτυ αδειάζει τη μεταβλητή.
    itself = "%s/book-appointment" % (current() or "").rstrip("/")
    target = "" if url.rstrip("/") == itself else url
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
    KEEP = booking()
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

    # Η κάρτα QR τυπώνει τη διεύθυνση και ως σκέτο κείμενο, χωρίς σχήμα — το PAT
    # ζητά https://, οπότε δεν την πιάνει και θα έμενε η παλιά κάτω από το QR.
    p = os.path.join(ROOT, "tools", "make-review-card.py")
    s = old_card = io.open(p, encoding="utf-8").read()
    s, k = re.subn(r'^SHOWN = "[^"]*"', 'SHOWN = "%s"' % host, s, count=1,
                   flags=re.M)
    if s != old_card:
        io.open(p, "w", encoding="utf-8").write(s)
    print("%-30s %d τυπωμένη διεύθυνση" % ("tools/make-review-card.py", k))

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
