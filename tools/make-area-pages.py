#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Φτιάχνει τις σελίδες περιοχής και τις γράφει στο sitemap.

  python3 tools/make-area-pages.py

Γιατί υπάρχουν αυτές οι σελίδες: ο ασθενής δεν ψάχνει «ωτορινολαρυγγολόγος».
Ψάχνει «ωτορινολαρυγγολόγος Νίκαια». Η αρχική σελίδα μιλά για τον Κορυδαλλό,
οπότε για κάθε γειτονική περιοχή χρειάζεται μια σελίδα που απαντά στη δική της
ερώτηση: πού είναι το ιατρείο, πώς θα φτάσω, τι θα γίνει όταν έρθω.

Γιατί γεννιούνται από κώδικα και δεν γράφονται στο χέρι: το τηλέφωνο, η
διεύθυνση και το ωράριο επαναλαμβάνονται σε τέσσερις σελίδες συν τα δομημένα
δεδομένα τους. Γραμμένα στο χέρι, μια αλλαγή ωραρίου θα ξεχνιόταν κάπου — και
ένα λάθος ωράριο στη Google είναι χειρότερο από καθόλου ωράριο.

Οι σελίδες λένε την αλήθεια: το ιατρείο είναι ΕΝΑ, στον Κορυδαλλό. Οι σελίδες
των άλλων περιοχών δεν υπονοούν παράρτημα — εξηγούν τη διαδρομή.
"""
import io
import os
import re
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Στοιχεία που επαναλαμβάνονται παντού. Μία πηγή αλήθειας. ---------------
PHONE_TEXT = "211 418 27 37"
PHONE_HREF = "2114182737"
PHONE_INTL = "+302114182737"
MOBILE_TEXT = "6936 503 658"
MOBILE_HREF = "6936503658"
EMAIL = "lmariolis@entclinic.gr"
STREET = "Δ. Διαμαντίδη 6 & Πλ. Ελευθερίας 10"
CITY = "Κορυδαλλός"
POSTAL = "18120"
HOURS_TEXT = ("Δευτέρα, Τρίτη, Πέμπτη 09:00–21:00 · "
              "Τετάρτη, Παρασκευή 09:00–20:00")
# Οι συντεταγμένες, όχι το κείμενο της διεύθυνσης: το «Δ. Διαμαντίδη 6 &
# Πλ. Ελευθερίας 10» είναι γωνία δύο δρόμων και γεωκωδικοποιείται αναξιόπιστα.
COORDS = "37.9772195%2C23.6490417"
MAPS = ("https://www.google.com/maps/place/%CE%94.%20%CE%94%CE%B9%CE%B1%CE%BC"
        "%CE%B1%CE%BD%CF%84%CE%AF%CE%B4%CE%B7%206%20%26%20%CE%A0%CE%BB.%20"
        "%CE%95%CE%BB%CE%B5%CF%85%CE%B8%CE%B5%CF%81%CE%AF%CE%B1%CF%82%2010%2C%20"
        "%CE%9A%CE%BF%CF%81%CF%85%CE%B4%CE%B1%CE%BB%CE%BB%CF%8C%CF%82%2018120/"
        "@37.9772195,23.6490417,17z")
# Το /maps/dir/ ΧΩΡΙΣ origin: οι Χάρτες συμπληρώνουν μόνοι τους την τοποθεσία
# του επισκέπτη. Χωρίς dir_action=navigate — δεν ξεκινά μόνη της φωνητική
# πλοήγηση σε κάποιον που απλώς κοιτάζει πού είναι το ιατρείο.
DIR = ("https://www.google.com/maps/dir/?api=1&amp;destination=" + COORDS +
       "&amp;travelmode=")
# Το σύντομο link του ιατρείου: δείχνει στην ίδια την καταχώριση στους
# Χάρτες, όχι σε συντεταγμένες. Τα τσιπ κρατούν το DIR, γιατί μόνο εκείνο
# δέχεται παράμετρο μέσου μεταφοράς.
SHORT = "https://maps.app.goo.gl/2Zwkrue6Wv7vSznw6?g_st=ac"

# Ποιο μέσο προτείνεται πρώτο σε κάθε περιοχή. Δεν είναι διακοσμητικό: είναι
# ό,τι λέει ήδη η ενότητα «Πώς θα έρθετε» της ίδιας σελίδας.
MODES = [("driving", "Με αυτοκίνητο"), ("transit", "Με ΜΜΜ"),
         ("walking", "Με τα πόδια")]


def site_base():
    """Η διεύθυνση του ιστότοπου, όπως τη δηλώνει το canonical της αρχικής."""
    s = io.open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r'<link rel="canonical" href="([^"]+?)/?"', s)
    return (m.group(1) if m else "https://entclinic.gr").rstrip("/")


# --- Οι περιοχές -----------------------------------------------------------
# Οι πτώσεις γράφονται μία-μία: η ελληνική κλίση δεν παράγεται με κανόνα, και
# ένα «στην Πειραιά» στην πρώτη γραμμή της σελίδας κοστίζει την εμπιστοσύνη.
AREAS = [
    dict(
        slug="korydallos", mode="walking", nom="Κορυδαλλός", loc="στον Κορυδαλλό",
        acc="τον Κορυδαλλό", short="στην Πλατεία Ελευθερίας",
        gen="Κορυδαλλού", frm="από τον Κορυδαλλό", home=True,
        blurb="Το ιατρείο βρίσκεται στην Πλατεία Ελευθερίας, στο κέντρο "
              "του Κορυδαλλού.",
        travel=[
            "Το ιατρείο είναι στη συμβολή της Δ. Διαμαντίδη με την Πλατεία "
            "Ελευθερίας, στην καρδιά του Κορυδαλλού.",
            "Με το Μετρό: σταθμός «Κορυδαλλός», Γραμμή 3. Η πλατεία "
            "εξυπηρετείται και από τις αστικές γραμμές που περνούν από το "
            "κέντρο του δήμου.",
            "Με τα πόδια: για τις γειτονιές γύρω από την πλατεία, το ιατρείο "
            "είναι θέμα λίγων λεπτών.",
        ],
        faq=[
            ("Πού ακριβώς είναι το ιατρείο μέσα στον Κορυδαλλό;",
             "Στη Δ. Διαμαντίδη 6, στη γωνία με την Πλατεία Ελευθερίας — "
             "στο κέντρο του δήμου, δίπλα στην πλατεία."),
            ("Υπάρχει Μετρό κοντά;",
             "Ναι. Ο σταθμός «Κορυδαλλός» της Γραμμής 3 εξυπηρετεί την "
             "περιοχή και συνδέει τον Κορυδαλλό με τη Νίκαια, τον Πειραιά "
             "και το κέντρο της Αθήνας."),
        ],
    ),
    dict(
        slug="nikaia", mode="transit", nom="Νίκαια", loc="στη Νίκαια",
        acc="τη Νίκαια", short="μία στάση Μετρό από τη Νίκαια",
        gen="Νίκαιας", frm="από τη Νίκαια", home=False,
        blurb="Η Νίκαια συνορεύει με τον Κορυδαλλό: το ιατρείο απέχει "
              "μία στάση Μετρό.",
        travel=[
            "Με το Μετρό: οι σταθμοί «Νίκαια» και «Κορυδαλλός» είναι "
            "διαδοχικοί στη Γραμμή 3 — μία στάση.",
            "Με αυτοκίνητο: οι δύο δήμοι είναι όμοροι, οπότε η διαδρομή "
            "είναι σύντομη ακόμη και σε ώρα αιχμής.",
            "Από τις γειτονιές της Νίκαιας που ακουμπούν στα όρια του "
            "Κορυδαλλού, η απόσταση καλύπτεται και με τα πόδια.",
        ],
        faq=[
            ("Έχετε ιατρείο μέσα στη Νίκαια;",
             "Όχι. Το ιατρείο είναι ένα, στον Κορυδαλλό, στη Δ. Διαμαντίδη 6 "
             "και Πλ. Ελευθερίας 10 — μία στάση Μετρό από τη Νίκαια."),
            ("Πόσο κρατά η διαδρομή από τη Νίκαια;",
             "Οι δύο δήμοι είναι γειτονικοί και οι σταθμοί Μετρό διαδοχικοί, "
             "οπότε η μετακίνηση είναι από τις συντομότερες του λεκανοπεδίου."),
        ],
    ),
    dict(
        slug="peiraias", mode="transit", nom="Πειραιάς", loc="στον Πειραιά",
        acc="τον Πειραιά", short="τρεις στάσεις Μετρό από τον Πειραιά",
        gen="Πειραιά", frm="από τον Πειραιά", home=False,
        blurb="Ο Κορυδαλλός συνδέεται με τον Πειραιά απευθείας με τη "
              "Γραμμή 3 του Μετρό.",
        travel=[
            "Με το Μετρό: από τον σταθμό «Πειραιάς» της Γραμμής 3, ο "
            "«Κορυδαλλός» είναι τρεις στάσεις — Μανιάτικα, Νίκαια, "
            "Κορυδαλλός.",
            "Με αυτοκίνητο: μέσω της Γρ. Λαμπράκη και της Π. Ράλλη προς το "
            "κέντρο του Κορυδαλλού.",
            "Ο ιατρός είναι μέλος του Ιατρικού Συλλόγου Πειραιά "
            "(αρ. μητρώου ιατρού 9251, ιατρείου 3181).",
        ],
        faq=[
            ("Έχετε ιατρείο μέσα στον Πειραιά;",
             "Όχι. Το ιατρείο είναι στον Κορυδαλλό, τρεις στάσεις Μετρό από "
             "τον σταθμό «Πειραιάς» της Γραμμής 3."),
            ("Ανήκετε στον Ιατρικό Σύλλογο Πειραιά;",
             "Ναι. Αριθμός μητρώου ιατρού 9251 και ιατρείου 3181 στον "
             "Ιατρικό Σύλλογο Πειραιά."),
        ],
    ),
    dict(
        slug="peristeri", mode="driving", nom="Περιστέρι", loc="στο Περιστέρι",
        acc="το Περιστέρι", short="οδικώς από το Περιστέρι μέσω Λεωφ. Θηβών",
        gen="Περιστερίου", frm="από το Περιστέρι", home=False,
        blurb="Από το Περιστέρι η συντομότερη διαδρομή προς τον Κορυδαλλό "
              "είναι οδικώς, μέσω της Λεωφόρου Θηβών.",
        travel=[
            "Με αυτοκίνητο: μέσω της Λεωφόρου Θηβών προς τα νότια και "
            "κατόπιν προς το κέντρο του Κορυδαλλού. Είναι η διαδρομή που "
            "επιλέγουν οι περισσότεροι ασθενείς από το Περιστέρι.",
            "Με το Μετρό: το Περιστέρι εξυπηρετείται από τη Γραμμή 2 και ο "
            "Κορυδαλλός από τη Γραμμή 3, οπότε η διαδρομή απαιτεί αλλαγή "
            "γραμμής και είναι αισθητά μακρύτερη από την οδική.",
            "Για ραντεβού την ίδια ημέρα, τηλεφωνήστε πριν ξεκινήσετε ώστε "
            "να μη χρειαστεί να περιμένετε.",
        ],
        faq=[
            ("Έχετε ιατρείο μέσα στο Περιστέρι;",
             "Όχι. Το ιατρείο είναι στον Κορυδαλλό, στη Δ. Διαμαντίδη 6 και "
             "Πλ. Ελευθερίας 10."),
            ("Πώς έρχονται οι ασθενείς από το Περιστέρι;",
             "Συνήθως οδικώς, μέσω της Λεωφόρου Θηβών. Με τα μέσα, η "
             "διαδρομή απαιτεί αλλαγή από τη Γραμμή 2 στη Γραμμή 3."),
        ],
    ),
]

# Ερωτήσεις που ισχύουν παντού, ίδιες σε κάθε σελίδα.
COMMON_FAQ = [
    ("Δέχεστε παιδιά;",
     "Ναι. Ο ιατρός είναι Χειρουργός Ωτορινολαρυγγολόγος Παίδων και "
     "Ενηλίκων, και το ιατρείο διαθέτει εξοπλισμό για παιδιατρικές εξετάσεις."),
    ("Χρειάζεται ραντεβού;",
     "Ναι, ώστε να μη χρειαστεί να περιμένετε. Για επείγοντα περιστατικά "
     "τηλεφωνήστε στο %s και θα βρεθεί χρόνος την ίδια ημέρα." % PHONE_TEXT),
]

EXAMS = ["Ωτομικροσκόπηση", "Ωτοενδοσκόπηση", "Ενδοσκόπηση μύτης",
         "Ενδοσκόπηση λάρυγγος", "Ακοολογικός έλεγχος", "Έλεγχος λαβύρινθου",
         "Έλεγχος δυσφαγίας", "Εξετάσεις για παιδιά"]

URGENT = [
    "Αιφνίδια πτώση της ακοής στο ένα αυτί — το πρώτο 72ωρο κρίνει τη θεραπεία.",
    "Έντονος ίλιγγος που δεν υποχωρεί, με έμετο ή αστάθεια στο βάδισμα.",
    "Βράγχος φωνής που επιμένει πάνω από τρεις εβδομάδες.",
    "Δυσκολία στην κατάποση ή στην αναπνοή, ή διόγκωση στον τράχηλο που "
    "μεγαλώνει.",
    "Πόνος στο αυτί με πυρετό σε παιδί, ή έκκριση από το αυτί.",
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def jstr(s):
    """Ασφαλές string για JSON-LD."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def page(area, base):
    url = "%s/%s/" % (base, area["slug"])
    home = area["home"]
    nom, loc, gen, frm = area["nom"], area["loc"], area["gen"], area["frm"]

    # Η σελίδα του Κορυδαλλού λέει «στον Κορυδαλλό» — εκεί είναι το ιατρείο.
    # Οι υπόλοιπες λένε «για τη Νίκαια», γιατί το ιατρείο δεν είναι εκεί.
    h1 = ("Ωτορινολαρυγγολόγος (ΩΡΛ) %s" % loc if home
          else "Ωτορινολαρυγγολόγος (ΩΡΛ) για %s" % area["acc"])
    title = ("ΩΡΛ %s — Λ. Μαριόλης, MD, MSc | %s"
             % (nom, "Ωτορινολαρυγγολογικό Ιατρείο" if home
                else "Ιατρείο στον Κορυδαλλό"))
    desc = ("Ωτορινολαρυγγολόγος %s — ιατρείο Λ. Μαριόλη, MD, MSc, %s. "
            "Ακοολογικός έλεγχος, ενδοσκόπηση, παιδο-ΩΡΛ, χειρουργική. "
            "Τηλ. %s." % (loc if home else "για %s" % area["acc"],
                          area["short"], PHONE_TEXT))

    faq = area["faq"] + COMMON_FAQ

    nearby = "".join(
        '<li><a href="../%s/">%s</a></li>' % (a["slug"], esc(a["nom"]))
        for a in AREAS if a["slug"] != area["slug"])

    travel = "\n".join("      <p>%s</p>" % esc(t) for t in area["travel"])
    exams = "".join("<li>%s</li>" % esc(e) for e in EXAMS)
    urgent = "".join("<li>%s</li>" % esc(u) for u in URGENT)
    # Τα υπόλοιπα μέσα μπαίνουν μετά το προτεινόμενο, ώστε το πρώτο τσιπ να
    # συμφωνεί με ό,τι μόλις διάβασε ο επισκέπτης στο «Πώς θα έρθετε».
    modes = ([(m, lbl) for m, lbl in MODES if m == area["mode"]] +
             [(m, lbl) for m, lbl in MODES if m != area["mode"]])
    mode_html = "".join(
        '<li><a href="%s%s" target="_blank" rel="noopener">%s</a></li>'
        % (DIR, m, esc(lbl)) for m, lbl in modes)

    faq_html = "\n".join(
        "      <details>\n"
        "        <summary>%s</summary>\n"
        "        <p>%s</p>\n"
        "      </details>" % (esc(q), esc(a)) for q, a in faq)
    faq_ld = ",\n".join(
        '      { "@type": "Question", "name": "%s",\n'
        '        "acceptedAnswer": { "@type": "Answer", "text": "%s" } }'
        % (jstr(q), jstr(a)) for q, a in faq)

    return """<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:locale" content="el_GR">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{base}/assets/social-card.jpg">
<link rel="icon" href="../assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="../assets/favicon.png">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<meta name="theme-color" content="#2E1D12">
<link rel="stylesheet" href="../assets/legal.css">
<link rel="stylesheet" href="../assets/area.css">
<link rel="stylesheet" href="../assets/map-button.css">

<!-- Δομημένα δεδομένα: η σελίδα δεν δηλώνει δεύτερο ιατρείο. Παραπέμπει στο
     ένα και μοναδικό, με @id ίδιο με της αρχικής, και προσθέτει μόνο την
     περιοχή που εξυπηρετεί και τις ερωτήσεις αυτής της σελίδας. -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@graph": [
    {{
      "@type": "MedicalWebPage",
      "@id": "{url}#page",
      "url": "{url}",
      "name": "{title_j}",
      "description": "{desc_j}",
      "inLanguage": "el",
      "isPartOf": {{ "@type": "WebSite", "url": "{base}/" }},
      "about": {{ "@id": "{base}/#iatreio" }},
      "breadcrumb": {{ "@id": "{url}#breadcrumb" }}
    }},
    {{
      "@type": "BreadcrumbList",
      "@id": "{url}#breadcrumb",
      "itemListElement": [
        {{ "@type": "ListItem", "position": 1, "name": "Αρχική", "item": "{base}/" }},
        {{ "@type": "ListItem", "position": 2, "name": "{nom_j}", "item": "{url}" }}
      ]
    }},
    {{
      "@type": "Physician",
      "@id": "{base}/#iatreio",
      "name": "Λάμπρος Μαριόλης, MD, MSc — Ωτορινολαρυγγολόγος",
      "url": "{base}/",
      "medicalSpecialty": "Otolaryngologic",
      "telephone": "{intl}",
      "email": "{email}",
      "address": {{
        "@type": "PostalAddress",
        "streetAddress": "{street_j}",
        "addressLocality": "{city}",
        "postalCode": "{postal}",
        "addressRegion": "Αττική",
        "addressCountry": "GR"
      }},
      "areaServed": {{ "@type": "City", "name": "{nom_j}" }},
      "openingHoursSpecification": [
        {{ "@type": "OpeningHoursSpecification", "dayOfWeek": ["Monday","Tuesday","Thursday"], "opens": "09:00", "closes": "21:00" }},
        {{ "@type": "OpeningHoursSpecification", "dayOfWeek": ["Wednesday","Friday"], "opens": "09:00", "closes": "20:00" }}
      ]
    }},
    {{
      "@type": "FAQPage",
      "@id": "{url}#faq",
      "mainEntity": [
{faq_ld}
      ]
    }}
  ]
}}
</script>
</head>
<body>

<header class="legal">
  <div class="wrap">
    <div>
      <strong>Λ. Μαριόλης, MD, MSc</strong>
      <span>Ωτορινολαρυγγολογικό Ιατρείο (ΩΡΛ) · Κορυδαλλός</span>
    </div>
    <a href="../">← Αρχική σελίδα</a>
  </div>
</header>

<main>
  <div class="wrap">

    <p class="eyebrow">Περιοχές που εξυπηρετούμε · {nom}</p>
    <h1>{h1}</h1>
    <p class="lede">{blurb} Ο Δρ. Λάμπρος Μαριόλης, MD, MSc, Χειρουργός
    Ωτορινολαρυγγολόγος Παίδων και Ενηλίκων, δέχεται ασθενείς {frm} για
    παθήσεις αυτιού, μύτης και λαιμού, με σύγχρονο διαγνωστικό εξοπλισμό.</p>

    <div class="actions">
      <a class="btn btn-solid" href="tel:{phone_href}">Καλέστε {phone}</a>
      <a class="btn btn-outline" href="mailto:{email}">Στείλτε email</a>
    </div>

    <h2>Πώς θα έρθετε {frm}</h2>
{travel}

    <h2>Τι αντιμετωπίζουμε</h2>
    <div class="cards">
      <div class="card">
        <h3>Αυτί</h3>
        <p>Ακοή, ίλιγγος, λαβύρινθος, χρόνιες ωτίτιδες και λειτουργική
        χειρουργική του αυτιού.</p>
      </div>
      <div class="card">
        <h3>Μύτη</h3>
        <p>Ρινική απόφραξη, διάφραγμα, παραρρίνιες κοιλότητες και αλλεργική
        ρινίτιδα.</p>
      </div>
      <div class="card">
        <h3>Κεφαλή &amp; Τράχηλος</h3>
        <p>Φωνή, κατάποση, θυρεοειδής αδένας και χειρουργική κεφαλής και
        τραχήλου.</p>
      </div>
    </div>
    <p style="margin-top:18px;">Αναλυτικά για κάθε πάθηση, στην
    <a href="../#specialties">ενότητα των παθήσεων</a> της αρχικής σελίδας.</p>

    <h2>Εξετάσεις στο ιατρείο</h2>
    <ul class="two-col">{exams}</ul>
    <p>Οι χειρουργικές επεμβάσεις — αμυγδαλεκτομή, αδενοτομή, σωληνίσκοι
    αερισμού, τυμπανοπλαστική, ευθειασμός ρινικού διαφράγματος, ενδοσκοπική
    χειρουργική ρινός, μικρολαρυγγοσκόπηση, θυρεοειδεκτομή — περιγράφονται
    στην <a href="../#services">ενότητα εξετάσεων και επεμβάσεων</a>.</p>

    <div class="urgent">
      <h3>Πότε να έρθετε την ίδια ημέρα</h3>
      <ul>{urgent}</ul>
      <p style="margin-top:12px;">Σε απειλητική για τη ζωή κατάσταση καλέστε
      το <strong>166</strong>.</p>
    </div>

    <h2>Πού είναι το ιατρείο</h2>

    <a href="{short}" target="_blank" rel="noopener noreferrer" class="smart-map-button"
       aria-label="Οδηγίες προς το ιατρείο με τους Χάρτες Google — ανοίγει σε νέο παράθυρο">
      <div class="map-icon-wrapper">
        <svg class="google-pin-icon" viewBox="0 0 24 24" width="28" height="28" aria-hidden="true" focusable="false">
          <path fill="#EA4335" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
          <circle fill="#FFFFFF" cx="12" cy="9" r="2.5"/>
        </svg>
        <div class="mini-fold-map"></div>
      </div>
      <div class="button-text-content">
        <span class="button-main-title">ΟΔΗΓΗΣΕ ΜΕ</span>
        <span class="button-sub-title">ΣΤΟ ΙΑΤΡΕΙΟ <span class="arrow-icon">›</span></span>
      </div>
    </a>
    <p class="gmaps-help">Ανοίγει τους Χάρτες Google — σε κινητό, απευθείας την
    εφαρμογή. Από κάτω, διαδρομή ανά μέσο μεταφοράς.</p>
    <ul class="gmaps-modes">{modes}
      <li><a href="{maps}" target="_blank" rel="noopener">Προβολή στον χάρτη</a></li>
    </ul>

    <dl class="nap">
      <div><dt>Διεύθυνση</dt><dd><a href="{maps}" target="_blank" rel="noopener">{street}, {city} {postal}</a></dd></div>
      <div><dt>Τηλέφωνο</dt><dd><a href="tel:{phone_href}">{phone}</a></dd></div>
      <div><dt>Κινητό</dt><dd><a href="tel:{mob_href}">{mob}</a></dd></div>
      <div><dt>Email</dt><dd><a href="mailto:{email}">{email}</a></dd></div>
      <div><dt>Ωράριο</dt><dd>{hours}</dd></div>
      <div><dt>Μητρώο</dt><dd>Ι.Σ. Πειραιά — αρ. μητρώου ιατρού 9251, ιατρείου 3181</dd></div>
    </dl>

    <h2>Συχνές ερωτήσεις</h2>
    <div class="faq">
{faq_html}
    </div>

    <h2>Επικοινωνήστε μαζί μας</h2>
    <p>Η σωστή διάγνωση ξεκινά με μία συζήτηση. Καλέστε μας ή στείλτε email —
    απαντάμε αυθημερόν.</p>
    <div class="actions">
      <a class="btn btn-solid" href="tel:{phone_href}">Καλέστε {phone}</a>
      <a class="btn btn-outline" href="mailto:{email}">Στείλτε email</a>
    </div>

    <h2>Άλλες περιοχές</h2>
    <ul class="nearby">{nearby}</ul>

  </div>
</main>

<footer class="legal">
  <div class="wrap">
    <span>© <span id="yr">2026</span> Λάμπρος Μαριόλης, MD, MSc — Ωτορινολαρυγγολόγος</span>
    <span><a href="../">Αρχική</a> · <a href="../privacy.html">Πολιτική Απορρήτου</a> · <a href="../terms.html">Όροι Χρήσης</a></span>
  </div>
</footer>

<script>document.getElementById('yr').textContent = new Date().getFullYear();</script>

</body>
</html>
""".format(
        title=esc(title), title_j=jstr(title),
        desc=esc(desc), desc_j=jstr(desc),
        url=url, base=base,
        nom=esc(nom), nom_j=jstr(nom), h1=esc(h1),
        blurb=esc(area["blurb"]), frm=esc(frm),
        travel=travel, exams=exams, urgent=urgent,
        faq_html=faq_html, faq_ld=faq_ld, nearby=nearby,
        dir=DIR, short=SHORT, modes=mode_html,
        phone=PHONE_TEXT, phone_href=PHONE_HREF, intl=PHONE_INTL,
        mob=MOBILE_TEXT, mob_href=MOBILE_HREF, email=EMAIL,
        street=esc(STREET), street_j=jstr(STREET), city=CITY, postal=POSTAL,
        hours=HOURS_TEXT, maps=MAPS)


def write_sitemap(base):
    """Ξαναγράφει τις εγγραφές των περιοχών, αφήνοντας τις υπόλοιπες ήσυχες."""
    p = os.path.join(ROOT, "sitemap.xml")
    s = io.open(p, encoding="utf-8").read()
    for a in AREAS:  # καθάρισμα τυχόν προηγούμενης εκτέλεσης
        s = re.sub(r"\s*<url><loc>[^<]*/%s/</loc>.*?</url>" % a["slug"],
                   "", s, flags=re.S)
    today = datetime.date.today().isoformat()
    rows = "".join(
        "\n  <url><loc>%s/%s/</loc><lastmod>%s</lastmod>"
        "<changefreq>monthly</changefreq><priority>0.8</priority></url>"
        % (base, a["slug"], today) for a in AREAS)
    s = s.replace("\n</urlset>", rows + "\n</urlset>")
    io.open(p, "w", encoding="utf-8").write(s)
    print("sitemap.xml                    %d σελίδες περιοχής" % len(AREAS))


def main():
    base = site_base()
    for a in AREAS:
        d = os.path.join(ROOT, a["slug"])
        if not os.path.isdir(d):
            os.makedirs(d)
        p = os.path.join(d, "index.html")
        io.open(p, "w", encoding="utf-8").write(page(a, base))
        print("%-30s %s/" % (a["slug"] + "/index.html", base + "/" + a["slug"]))
    write_sitemap(base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
