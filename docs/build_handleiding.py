"""Generates docs/FitTrick Handleiding.docx (upload to Google Drive -> converts to a Google Doc).

Usage: python -I docs/build_handleiding.py
Update VERSION/DATE and the text below when the app changes (see the sluit-af skill).
"""
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

VERSION = "1.0"
DATE = "11 november 2026"
APP_URL = "https://leurspclaurde-gif.github.io/FitTrick/"
REPO_URL = "https://github.com/leurspclaurde-gif/FitTrick"

ROOT = Path(__file__).resolve().parent.parent
ACCENT = RGBColor(0xB9, 0x77, 0x3F)
INK = RGBColor(0x2F, 0x2A, 0x24)

doc = Document()

# ---------- styles ----------
st = doc.styles
st["Normal"].font.name = "Arial"
st["Normal"].font.size = Pt(10.5)
st["Normal"].paragraph_format.space_after = Pt(6)
for name, size in (("Title", 28), ("Heading 1", 18), ("Heading 2", 13.5), ("Heading 3", 11.5)):
    s = st[name]
    s.font.name = "Arial"
    s.font.size = Pt(size)
    s.font.bold = True
    s.font.color.rgb = ACCENT if name != "Heading 3" else INK
    s.paragraph_format.keep_with_next = True
    s.paragraph_format.space_before = Pt(18 if name == "Heading 1" else 12)
    s.paragraph_format.space_after = Pt(6)
    rpr = s.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(a), "Arial")

sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
for side in ("left_margin", "right_margin"):
    setattr(sec, side, Cm(2.2))
sec.top_margin = sec.bottom_margin = Cm(2)


# ---------- helpers ----------
def p(text="", bold_prefix=None, style=None, italic=False):
    par = doc.add_paragraph(style=style)
    if bold_prefix:
        par.add_run(bold_prefix).bold = True
    r = par.add_run(text)
    r.italic = italic
    return par


def h1(t): doc.add_heading(t, level=1)
def h2(t): doc.add_heading(t, level=2)
def h3(t): doc.add_heading(t, level=3)


def bullets(items, style="List Bullet"):
    for it in items:
        if isinstance(it, tuple):
            p(it[1], bold_prefix=it[0], style=style)
        else:
            p(it, style=style)


def steps(items):
    bullets(items, style="List Number")


def code(text):
    for line in text.strip("\n").split("\n"):
        par = doc.add_paragraph()
        par.paragraph_format.space_after = Pt(0)
        par.paragraph_format.left_indent = Cm(0.6)
        r = par.add_run(line)
        r.font.name = "Consolas"
        r.font.size = Pt(9.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def note(text, label="Tip: "):
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Cm(0.4)
    pPr = par._p.get_or_add_pPr()
    bdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    for k, v in (("w:val", "single"), ("w:sz", "18"), ("w:space", "8"), ("w:color", "B9773F")):
        left.set(qn(k), v)
    bdr.append(left)
    pPr.append(bdr)
    r = par.add_run(label)
    r.bold = True
    r.font.color.rgb = ACCENT
    par.add_run(text)


def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(h)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), "B9773F")
        c._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
    for row in t.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Cm(w)
        for c in row.cells:
            for par in c.paragraphs:
                par.paragraph_format.space_after = Pt(2)
                for r in par.runs:
                    r.font.size = Pt(9.5)
    doc.add_paragraph()


def page_break():
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def toc():
    par = doc.add_paragraph()
    run = par.add_run()
    for tag, text in (("begin", None), (None, 'TOC \\o "1-2" \\h \\z \\u'), ("separate", None), (None, None), ("end", None)):
        if tag:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), tag)
            run._r.append(fc)
        elif text:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            run._r.append(it)
        else:
            t = OxmlElement("w:t")
            t.text = "Inhoudsopgave — in Google Docs: Invoegen › Inhoudsopgave (of klik op de inhoudsopgave › Vernieuwen)."
            run._r.append(t)


# ---------- title page ----------
doc.add_paragraph()
title = doc.add_paragraph(style="Title")
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.add_run("FitTrick Handleiding")
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sub.add_run("Gebruik, Google Sheets, GitHub en software-updates")
r.font.size = Pt(13)
r.font.color.rgb = INK
img = doc.add_paragraph()
img.alignment = WD_ALIGN_PARAGRAPH.CENTER
_png = ROOT / "docs" / "splash.png"
from PIL import Image  # python-docx cannot embed webp
Image.open(ROOT / "app" / "img" / "splash.webp").convert("RGB").save(_png)
img.add_run().add_picture(str(_png), height=Cm(13))
meta = doc.add_paragraph()
meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
meta.add_run(f"Versie {VERSION} · {DATE}\n").bold = True
meta.add_run(f"App: {APP_URL}")
page_break()

h1("Inhoud")
toc()
page_break()

# =====================================================================
h1("Deel 1 — Gebruikershandleiding")

h2("1. Wat is FitTrick?")
p("FitTrick is je persoonlijke trainingscoach op je iPhone. De app stelt elke training samen op basis van je schema "
  "(Push / Pull / Legs), de plaats waar je traint (fitness of thuis), de tijd die je hebt en wat je de voorbije dagen "
  "al getraind hebt. Tijdens de training begeleidt de app je oefening per oefening, met een rusttimer. Na afloop "
  "wordt elke set gelogd in je Google Sheet.")
bullets([
    ("Schema: ", "Push → Pull → Legs draait gewoon door. Een rustdag verandert de volgorde niet."),
    ("Slim voorstel: ", "spiergroepen die deze week nog weinig aan bod kwamen krijgen voorrang; oefeningen van de vorige "
     "gelijkaardige training worden afgewisseld."),
    ("Progressie: ", "haal je bij een oefening het maximum aantal herhalingen, dan stelt de app de volgende keer het "
     "eerstvolgende beschikbare gewicht voor."),
    ("Altijd buikspieren: ", "elke training eindigt met minstens één buikspieroefening."),
    ("Alles aanpasbaar: ", "oefeningen, sets, herhalingen, gewicht, volgorde en spiergroepen."),
])

h2("2. De app installeren op je iPhone")
steps([
    f"Open Safari (niet Chrome) en surf naar {APP_URL}",
    "Tik op Deel (vierkantje met pijl omhoog) › Zet op beginscherm › Voeg toe.",
    "Open FitTrick voortaan via het icoon op je beginscherm.",
    "De eerste keer: tik op het startscherm › ⚙ Instellingen › vul Gebruiker (Patrick), de Apps Script-URL en de token in "
    "› Opslaan & synchroniseren. (URL en token: zie deel 2, hoofdstuk 12.)",
])
note("De app op je beginscherm heeft zijn eigen geheugen, los van Safari. Vul de instellingen dus in de app zelf in.")

h2("3. Het hoofdscherm")
p("Na een tik op het startscherm kom je op het hoofdscherm:")
bullets([
    ("Locatie: ", "Fitness of Thuis. Thuis krijg je enkel oefeningen met je halters, je mat of je lichaamsgewicht."),
    ("Schema: ", "Push, Pull, Legs of Full body. De app markeert de volgende dag in je rotatie met ‘volgende’."),
    ("Duur: ", "met − en + pas je de trainingsduur aan per 15 minuten."),
    ("Stel training voor: ", "maakt een voorstel op maat."),
    ("Cardio loggen / Historiek: ", "zie hoofdstuk 6 en 7."),
    ("Training bezig: ", "is er een training onderbroken (bv. app afgesloten), dan kan je ze hier hervatten."),
])
p("Bovenaan zie je wanneer de app laatst gesynchroniseerd is en of er nog trainingen wachten om verstuurd te worden.")

h2("4. Het trainingsvoorstel")
p("Het voorstel toont per oefening de spiergroepen, sets × herhalingen × gewicht, de geschatte duur en wat je de "
  "vorige keer deed (oranje). Bovenaan staat de totale geschatte duur ten opzichte van je gekozen duur.")
table(["Knop", "Wat doet het?"], [
    ["−15 / +15", "Duur aanpassen; het voorstel wordt opnieuw berekend (zelfde basis, meer of minder oefeningen)."],
    ["Spiergroepen", "Kies zelf welke spieren aan bod komen (ook over Push/Pull/Legs heen) › Nieuw voorstel."],
    ["🎲 Ander voorstel", "Een volledig nieuw voorstel met andere oefeningen."],
    ["✎ Aanpassen", "Sets, herhalingen en gewicht wijzigen; ‘+ set’ en ✕ per set. Een wijziging geldt ook voor de volgende sets."],
    ["⇄ Wissel", "Kies een alternatief; eerst oefeningen voor dezelfde spier, met zoekveld en spiergroep-filter."],
    ["↑ ↓", "Volgorde wijzigen."],
    ["✕", "Oefening verwijderen."],
    ["+ Oefening toevoegen", "Elke oefening die op je locatie mogelijk is (meest gebruikte eerst)."],
    ["Start training", "Start de begeleiding. Ontbreekt er nog een gewicht (nieuwe oefening), dan krijg je een melding."],
], [4, 12.6])
note("Gewichten volgen wat er op je locatie bestaat. Thuis zijn dat 2,5 – 16,5 kg per halter (twee halters) of tot "
     "30,5 kg met één halter. Bij oefeningen met twee halters is het gewicht altijd per halter.")

h2("5. Tijdens de training")
steps([
    "Je ziet één oefening tegelijk, met een korte uitleg en je vorige prestatie.",
    "Pas indien nodig gewicht (− / +) en herhalingen aan, of tik op het getal om het te typen.",
    "Tik op ✓ na elke set. De rusttimer start automatisch onderaan (+15s of Overslaan). Op het einde hoor je een signaal.",
    "Na de laatste set gaat de app automatisch naar de volgende oefening. Met ‹ Vorige / Volgende › of de lijst onderaan "
    "spring je zelf naar een oefening.",
    "⇄ Wissel oefening (bv. toestel bezet) en + Oefening kan ook tijdens de training.",
    "Klaar? Tik op ⏹ of Afronden › bekijk de samenvatting › eventueel een notitie › Opslaan in log.",
])
p("Enkel afgevinkte sets worden gelogd. Heb je geen netwerk, dan wordt de training op je iPhone bewaard en "
  "automatisch verstuurd zodra er weer verbinding is (of via Instellingen › Wachtrij versturen).")
note("Laat het geluid van je iPhone aan staan voor het rustsignaal. Het scherm blijft tijdens een training normaal "
     "aan (afhankelijk van je iOS-versie).")

h2("6. Cardio en wandelen loggen")
p("Hoofdscherm › 🚶 Cardio loggen › kies de activiteit (bv. Walking), datum/tijd, duur in minuten en eventueel de "
  "afstand in km › Opslaan. Het wordt gelogd in dezelfde Log-sheet.")

h2("7. Historiek")
p("Toont je trainingen van de laatste 70 dagen. Tik op een training voor alle sets. De volledige historiek "
  "(sinds oktober 2023) staat in de Google Sheet ‘FitTrick Log Patrick’.")

h2("8. Instellingen en synchroniseren")
bullets([
    ("Gebruiker: ", "bepaalt in welke log-sheet gelogd wordt (FitTrick Log <Gebruiker>)."),
    ("Apps Script-URL en Token: ", "de koppeling met je Google Sheets."),
    ("Opslaan & synchroniseren: ", "haalt de bibliotheek en je historiek opnieuw op. Doe dit na een wijziging in de "
     "FitTrick Library. (Bij het opstarten synchroniseert de app ook automatisch.)"),
    ("Wachtrij versturen: ", "verstuurt trainingen die nog niet in Google Sheets staan."),
])

# =====================================================================
page_break()
h1("Deel 2 — De Google Sheets")

h2("9. Overzicht")
p("FitTrick gebruikt twee Google Sheets in je privé Google Drive, plus een klein script (Apps Script) dat de app met "
  "de sheets verbindt:")
table(["Bestand", "Inhoud", "Wie past aan?"], [
    ["FitTrick Library", "Oefeningen, materiaal per locatie, gewichten, spiergroepen, instellingen. Bevat ook het Apps Script.",
     "Jij (de app leest)"],
    ["FitTrick Log Patrick", "Elke set van elke training, inclusief je volledige historiek.", "De app (jij leest)"],
], [4, 9, 3.6])
note("De namen moeten exact zo blijven: het script zoekt de log op naam (‘FitTrick Log ’ + gebruiker).", "Belangrijk: ")

h2("10. FitTrick Library — tabbladen")
h3("Exercises (oefeningen)")
table(["Kolom", "Betekenis"], [
    ["Exercise", "Naam (Engels). Moet uniek zijn; gebruik dezelfde naam als in de log, anders verlies je de koppeling met je historiek."],
    ["Active", "FALSE = oefening verschijnt niet meer in voorstellen, wissel- en toevoeglijsten."],
    ["Day", "Berekend uit Primary (tab Muscles): Push / Pull / Legs / Core / Cardio / Mobility. Niet aanpassen."],
    ["Primary / Secondary", "Primaire spiergroep en tot 3 secundaire (gescheiden door ;). Kies uit de tab Muscles."],
    ["Equipment", "Al het nodige materiaal, gescheiden door ; (bv. Dumbbell; Bench). Bepaalt op welke locatie de oefening kan."],
    ["Load", "Het materiaal waarvan je het gewicht ingeeft (None = geen gewicht)."],
    ["Implements", "2 = twee halters/kettlebells tegelijk (gewicht per stuk), 1 = één, 0 = geen."],
    ["Type", "Weighted, Bodyweight, Timed (RepMin–RepMax in seconden) of Cardio (in minuten)."],
    ["Mechanics", "Compound (meerdere gewrichten, komt eerst) of Isolation."],
    ["RepMin / RepMax", "Herhalingsbereik voor de progressie."],
    ["Sets / RestSec / SecPerRep", "Standaard aantal sets, rust tussen sets (s) en tempo per herhaling (s): bepalen de geschatte duur."],
    ["Added / Instructions", "Toegevoegd door Claude (Yes) / korte uitleg die in de app verschijnt."],
], [4, 12.6])
h3("Equipment (materiaal per locatie)")
table(["Kolom", "Betekenis"], [
    ["Location / Equipment", "Gym of Home + het materiaal."],
    ["Available", "TRUE = aanwezig op die locatie."],
    ["Loading", "Fixed = lijst vaste gewichten · Stack = van min tot max per stap · Plates = stang + schijven · None = geen gewicht."],
    ["Bar kg", "Gewicht van de stang (Plates). Thuis: halterstang 2,5 kg."],
    ["Fixed weights", "Bij Fixed: beschikbare gewichten, gescheiden door komma (bv. 10, 15, 20, 25)."],
    ["Stack min / max / step", "Bij Stack: kleinste, grootste gewicht en de stap (bv. 5 – 200 per 2,5)."],
], [4, 12.6])
h3("Plates (schijven)")
p("Per locatie en toestel de schijven en het totale aantal. Thuis: 4 × 1 kg, 4 × 2 kg en 4 × 4 kg voor de halters "
  "(samen voor beide halters). In de fitness betekent Equipment ‘*’: voor alle toestellen met Loading = Plates.")
h3("Muscles en Settings")
bullets([
    ("Muscles: ", "per spiergroep de dag in het schema, het gewenste aantal sets per week en een prioriteit (0–1). "
     "Hogere prioriteit of meer sets per week = vaker voorgesteld. De volgorde van de rijen is ook de volgorde in de training."),
    ("Settings: ", "PPL Order (volgorde van het schema), Default minutes, Duration step (15), Transition sec (tijd per "
     "oefening voor opstellen), Min core exercises (1), Weekly window days (7) en Variety sessions (2)."),
])
h3("Voorbeelden")
bullets([
    ("Je koopt een kettlebell van 12 kg: ", "tab Equipment › rij Home / Kettlebell › Available = TRUE, Loading = Fixed, "
     "Fixed weights = 12. In de app: Instellingen › Opslaan & synchroniseren. Kettlebell-oefeningen worden nu thuis voorgesteld."),
    ("Je koopt extra schijven van 2,5 kg: ", "tab Plates › nieuwe rij Home | Dumbbell | 2.5 | 4."),
    ("Een bank voor thuis: ", "Equipment › Home / Bench › Available = TRUE (bankdrukken met halters wordt mogelijk)."),
    ("Je wil een oefening nooit meer zien: ", "Exercises › Active = FALSE."),
    ("Nieuwe oefening: ", "voeg onderaan een rij toe in Exercises en vul minstens Exercise, Active, Primary, Equipment, "
     "Load, Implements, Type, Mechanics, RepMin, RepMax, Sets, RestSec en SecPerRep in."),
    ("De halters in de fitness gaan per 2,5 kg: ", "Equipment › Gym / Dumbbell › Fixed weights aanpassen."),
])
note("Wijzig geen kolomtitels en verwijder geen tabbladen: de app leest de kolommen op hun naam.", "Let op: ")

h2("11. FitTrick Log Patrick")
p("Eén rij per set. Kolommen: Date (UTC), Exercise, Reps, Weight(kg) (per halter bij twee halters), Duration(s), "
  "Distance(m), Incline, Resistance, isWarmup, Note, multiplier (aantal halters), Workout ID, Location, Day.")
bullets([
    "Je mag de log bekijken, filteren en er grafieken of draaitabellen van maken — liefst op een apart tabblad.",
    "Pas bestaande rijen niet aan en sorteer het tabblad niet: de app leest de laatste trainingen om voorstellen te maken.",
    "Een foutieve set verwijderen mag (volledige rij verwijderen).",
    "De historiek vóór FitTrick komt uit je Fitbod-export (sinds oktober 2023).",
])

h2("12. Het Apps Script (koppeling)")
p("Het script zit in FitTrick Library (Extensies › Apps Script) en werd eenmalig zo ingesteld:")
steps([
    "Code.gs plakken uit de projectmap (apps-script\\Code.gs) en opslaan.",
    "Functie setup uitvoeren (toestemming geven: Geavanceerd › Ga naar FitTrick). Het logboek toont de token.",
    "Implementeren › Nieuwe implementatie › Web-app · Uitvoeren als: Ik · Toegang: Iedereen › URL (eindigt op /exec) kopiëren.",
])
h3("Token of URL terugvinden")
bullets([
    ("Token: ", "Apps Script › ⚙ Projectinstellingen › Scripteigenschappen › TOKEN (of setup opnieuw uitvoeren: het logboek toont hem)."),
    ("URL: ", "Implementeren › Implementaties beheren › web-app-URL."),
    ("Nieuwe token (bv. als iemand hem kent): ", "Projectinstellingen › Scripteigenschappen › TOKEN verwijderen › setup "
     "uitvoeren › nieuwe token invullen in de app."),
])
note("‘Iedereen’ betekent enkel dat het adres bereikbaar is. Zonder de juiste token geeft het script niets terug en "
     "kan niemand iets loggen. Deel URL en token met niemand.", "Veiligheid: ")

# =====================================================================
page_break()
h1("Deel 3 — Technisch beheer")

h2("13. Hoe zit het in elkaar?")
code("""
iPhone (FitTrick web-app)  ⇄  Apps Script (web-app)  ⇄  Google Sheets
   GitHub Pages                  in FitTrick Library      FitTrick Library + FitTrick Log Patrick
""")
bullets([
    ("De app ", "is een Progressive Web App (PWA): een website die zich als app gedraagt en offline werkt. Ze bestaat "
     "uit gewone HTML/CSS/JavaScript-bestanden zonder build-stap."),
    ("GitHub Pages ", f"host die bestanden gratis via https ({APP_URL})."),
    ("Apps Script ", "is de ‘backend’: het levert de bibliotheek en je historiek aan de app en schrijft trainingen in de log."),
])

h2("14. De projectmap op je pc (C:\\Claude\\FitTrick)")
table(["Map / bestand", "Inhoud", "Op GitHub?"], [
    ["app\\", "De app zelf (index.html, css, js, afbeeldingen, sw.js).", "Ja"],
    ["apps-script\\Code.gs", "Code voor het Apps Script.", "Ja"],
    [".github\\workflows\\pages.yml", "Automatische publicatie naar GitHub Pages.", "Ja"],
    ["tests\\", "Automatische tests van de voorstel-logica.", "Ja"],
    ["tools\\", "Scripts die de eerste versie van de sheets bouwden.", "Ja"],
    ["docs\\", "Deze handleiding en het script dat ze maakt.", "Ja"],
    ["CLAUDE.md, .claude\\", "Projectgeheugen en het ‘sluit af’-commando voor Claude.", "Ja"],
    ["SETUP.md", "Korte installatiegids.", "Ja"],
    ["Trainingen Patrick.csv, sheets\\, dev-data\\", "Je persoonlijke data.", "Nee (afgeschermd)"],
], [5, 8.6, 3])

h2("15. GitHub en GitHub Pages")
bullets([
    ("Account: ", "leurspclaurde-gif · repository: FitTrick (publiek; nodig voor gratis Pages)."),
    ("Repository: ", REPO_URL),
    ("Publicatie: ", "Settings › Pages › Source = GitHub Actions. Elke push naar de branch main die iets in app\\ "
     "wijzigt, start automatisch de workflow ‘Deploy FitTrick to GitHub Pages’ (± 1 minuut)."),
    ("Opvolgen: ", "tabblad Actions in de repository. Groen vinkje = online; rood kruisje = klik de run open › Re-run jobs, "
     "of vraag Claude de fout te bekijken."),
    ("Wat is publiek? ", "Alleen de code en het startscherm. Je data, de URL van het Apps Script en je token staan nooit "
     "op GitHub."),
    ("Commits ", "gebruiken het anonieme GitHub-adres leurspclaurde-gif@users.noreply.github.com."),
])

h2("16. Een software-update doorvoeren")
h3("Gewone werkwijze (met Claude)")
steps([
    "Open een sessie in Claude Code in de map C:\\Claude\\FitTrick en beschrijf wat je wil (bv. ‘voeg grafieken per oefening toe’). "
    "Claude leest CLAUDE.md en kent zo de volledige context.",
    "Claude past de code aan, test lokaal (automatische tests + de app in een testbrowser met testdata) en verhoogt het "
    "versienummer in app\\sw.js zodat je iPhone de nieuwe versie ophaalt.",
    "Na jouw akkoord commit en pusht Claude naar GitHub. De workflow publiceert automatisch.",
    "Op je iPhone: sluit FitTrick volledig (omhoog vegen) en open opnieuw. Soms is dit twee keer nodig.",
    "Typ ‘sluit af’ op het einde van de sessie: Claude werkt CLAUDE.md (en indien nodig deze handleiding) bij.",
])
h3("Wijzigingen aan het Apps Script (Code.gs)")
steps([
    "Open FitTrick Library › Extensies › Apps Script en vervang de code door de nieuwe apps-script\\Code.gs › Opslaan.",
    "Implementeren › Implementaties beheren › ✎ (potlood) › Versie: Nieuwe versie › Implementeren.",
    "De URL blijft dezelfde; in de app hoef je niets te wijzigen.",
])
note("Maak géén ‘Nieuwe implementatie’ aan voor een update: dan krijg je een nieuwe URL die je in de app opnieuw moet invullen.", "Let op: ")
h3("Wijzigingen aan de structuur van de sheets")
p("Komt er een nieuwe kolom of een nieuw tabblad bij, dan zegt Claude welke kolom je waar moet toevoegen (de app "
  "leest kolommen op naam, dus de plaats van een nieuwe kolom maakt niet uit).")
h3("Lokaal testen (voor wie zelf wil kijken)")
code("""
node --test tests/
python -m http.server 8321
-> open http://localhost:8321/app/?dev   (testdata, geen Google nodig)
""")

h2("17. Werken met Claude: CLAUDE.md en ‘sluit af’")
bullets([
    ("CLAUDE.md ", "is het projectgeheugen: wensen, architectuur, structuur van de sheets, hoe voorstellen berekend "
     "worden, aandachtspunten, status, ideeënlijst en een logboek per sessie. Claude leest het automatisch bij elke "
     "nieuwe sessie in deze map."),
    ("‘sluit af’ ", "(of /sluit-af): Claude werkt CLAUDE.md bij met wat er deze sessie gebeurde, controleert of deze "
     "handleiding moet aangepast worden, draait de tests en meldt wat nog niet gecommit/gepusht is."),
    ("Handleiding bijwerken: ", "Claude maakt een nieuwe docs\\FitTrick Handleiding.docx. Upload die naar Google Drive "
     "(met conversie aan) en vervang de oude Google Doc, of open de nieuwe en verwijder de oude."),
])

h2("18. Problemen oplossen")
table(["Probleem", "Oplossing"], [
    ["‘Ongeldige token’", "Token in de app vergelijken met Scripteigenschappen › TOKEN (zie 12)."],
    ["‘Log-sheet niet gevonden’", "Naam moet exact ‘FitTrick Log Patrick’ zijn (geen .xlsx) en in dezelfde Google-account staan."],
    ["Wijziging in de Library niet zichtbaar", "Instellingen › Opslaan & synchroniseren."],
    ["Training niet in de log", "Instellingen › Wachtrij versturen; controleer netwerk, URL en token."],
    ["Nieuwe app-versie verschijnt niet", "App volledig sluiten en heropenen (eventueel twee keer). Controleer op GitHub › Actions of de publicatie gelukt is."],
    ["Oefening nooit voorgesteld", "Active = TRUE? Is al het Equipment op die locatie Available? Hoort de Primary bij de gekozen dag?"],
    ["Gewicht klopt niet met de toestellen", "Tab Equipment: Fixed weights of Stack min/max/step aanpassen voor dat toestel."],
    ["Geen rustsignaal", "Stil-modus van de iPhone uit en volume omhoog; tik minstens één keer in de app vóór de eerste rust."],
    ["Fout na wijziging aan Code.gs", "Nieuwe versie van de bestaande implementatie gemaakt (zie 16)? Uitvoeringen bekijken in Apps Script › Uitvoeringen."],
], [5.5, 11.1])

h2("19. Privacy en back-up")
bullets([
    "Je trainingsdata staat enkel in je privé Google Drive en (tijdelijk) op je iPhone.",
    "Google Drive bewaart automatisch versiegeschiedenis van de sheets (Bestand › Versiegeschiedenis).",
    "Extra back-up: Bestand › Downloaden › Microsoft Excel van beide sheets, af en toe.",
    "Deel de Apps Script-URL en de token met niemand; de GitHub-repository bevat ze niet.",
])

out = ROOT / "docs" / "FitTrick Handleiding.docx"
doc.save(out)
print(out)
