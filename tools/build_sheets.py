"""Builds the FitTrick spreadsheets (to import in Google Drive) and dev test data.

Usage:  python -I tools/build_sheets.py
Input:  Trainingen Patrick.csv, tools/exercise_meta.csv
Output: sheets/FitTrick Library.xlsx, sheets/FitTrick Log Patrick.xlsx, dev-data/library.json, dev-data/history.json
"""
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parent.parent
USER = "Patrick"
HISTORY_CSV = ROOT / "Trainingen Patrick.csv"
META_CSV = ROOT / "tools" / "exercise_meta.csv"

MUSCLES = [  # muscle, day, weekly target sets, priority
    ("Chest", "Push", 14, 1.0), ("Front Delts", "Push", 6, 0.8), ("Side Delts", "Push", 10, 1.0), ("Triceps", "Push", 10, 1.0),
    ("Lats", "Pull", 12, 1.0), ("Upper Back", "Pull", 10, 1.0), ("Rear Delts", "Pull", 6, 0.8), ("Traps", "Pull", 4, 0.6),
    ("Biceps", "Pull", 10, 1.0), ("Forearms", "Pull", 3, 0.4), ("Lower Back", "Pull", 4, 0.7),
    ("Quads", "Legs", 12, 1.0), ("Hamstrings", "Legs", 10, 1.0), ("Glutes", "Legs", 10, 1.0), ("Adductors", "Legs", 4, 0.6),
    ("Abductors", "Legs", 4, 0.6), ("Calves", "Legs", 8, 0.8),
    ("Abs", "Core", 8, 1.0), ("Obliques", "Core", 4, 0.8),
    ("Cardio", "Cardio", 0, 0), ("Mobility", "Mobility", 0, 0),
]

SETTINGS = [
    ("User", USER, "Naam van de gebruiker; de log heet 'FitTrick Log <User>'."),
    ("PPL Order", "Push, Pull, Legs", "Volgorde van het schema; draait gewoon door (rustdagen tellen niet)."),
    ("Default minutes", 60, "Standaard trainingsduur in minuten."),
    ("Duration step", 15, "Stap (minuten) waarmee je de duur aanpast."),
    ("Transition sec", 90, "Tijd per oefening voor opstellen/wisselen (seconden)."),
    ("Min core exercises", 1, "Minimum aantal buikspieroefeningen op het einde van elke training."),
    ("Weekly window days", 7, "Periode (dagen) waarover het trainingsvolume per spiergroep geteld wordt."),
    ("Variety sessions", 2, "Oefeningen uit de laatste N trainingen van hetzelfde type krijgen minder voorrang."),
]

ALL_EQUIPMENT = ["Mat", "Dumbbell", "Barbell", "EZ-Bar", "Trap Bar", "Kettlebell", "Cable", "Machine", "Smith Machine",
                 "Leg Press", "Hack Squat", "Hammer Strength", "Bench", "Incline Bench", "Decline Bench", "Preacher Bench",
                 "Pull-up Bar", "Dip Station", "Landmine", "Medicine Ball", "Stability Ball", "Balance Trainer", "TRX",
                 "Plate", "Box", "Treadmill", "Bike", "Rower", "Elliptical", "Stair Stepper", "Battle Ropes", "Foam Roller",
                 "Ab Wheel", "Squat Rack"]

# Location, Equipment, Loading, Bar kg, Fixed weights, Stack min, Stack max, Stack step, Notes
GYM_LOADING = {
    "Dumbbell": ("Fixed", "", "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30", "", "", "", "Vaste halters (kg per halter)."),
    "EZ-Bar": ("Fixed", "", "10, 15, 20, 25, 30, 35, 40", "", "", "", "Vaste EZ-stangen."),
    "Kettlebell": ("Fixed", "", "4, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32", "", "", "", ""),
    "Medicine Ball": ("Fixed", "", "2, 3, 4, 5, 6, 8, 10, 12, 15", "", "", "", ""),
    "Plate": ("Fixed", "", "1.25, 2.5, 5, 10, 15, 20, 25", "", "", "", "Schijf in de hand."),
    "Barbell": ("Stack", "", "", 10, 200, 2.5, "Vaste en laadbare stangen samen: alles per 2,5 kg vanaf 10 kg."),
    "Cable": ("Stack", "", "", 2.5, 100, 2.5, "Kabel: pas stap aan als de toestellen in lb zijn."),
    "Machine": ("Stack", "", "", 5, 200, 2.5, "Toestellen met gewichtstapel; pas aan per fitness."),
    "Smith Machine": ("Plates", 0, "", "", "", "", "Gewicht = enkel de schijven."),
    "Trap Bar": ("Plates", 25, "", "", "", "", ""),
    "Leg Press": ("Plates", 0, "", "", "", "", "Gewicht = enkel de schijven."),
    "Hack Squat": ("Plates", 0, "", "", "", "", ""),
    "Hammer Strength": ("Plates", 0, "", "", "", "", ""),
    "Landmine": ("Plates", 0, "", "", "", "", "Gewicht = schijven op de stang."),
}
HOME_AVAILABLE = {"Mat", "Dumbbell"}


def read_meta():
    if not META_CSV.exists():
        sys.exit(f"{META_CSV} ontbreekt")
    with open(META_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(v):
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return v


def style_header(ws, widths):
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="B9773F")
        c.alignment = Alignment(vertical="center")
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def build_library(meta):
    wb = Workbook()

    # --- Exercises ---
    ws = wb.active
    ws.title = "Exercises"
    cols = ["Exercise", "Active", "Day", "Primary", "Secondary", "Equipment", "Load", "Implements", "Type", "Mechanics",
            "RepMin", "RepMax", "Sets", "RestSec", "SecPerRep", "Added", "Instructions"]
    ws.append(cols)
    for i, r in enumerate(meta, start=2):
        ws.append([r["Exercise"], True, f'=IFERROR(VLOOKUP(D{i},Muscles!A:B,2,FALSE),"")', r["Primary"], r["Secondary"],
                   r["Equipment"], r["Load"], num(r["Implements"]), r["Type"], r["Mechanics"], num(r["RepMin"]),
                   num(r["RepMax"]), num(r["Sets"]), num(r["RestSec"]), num(r["SecPerRep"]), r.get("Added", ""),
                   r["Instructions"]])
    n = len(meta) + 1
    dvs = [
        (f"D2:D{n + 200}", f"=Muscles!$A$2:$A${len(MUSCLES) + 1}"),
        (f"I2:I{n + 200}", '"Weighted,Bodyweight,Timed,Cardio"'),
        (f"J2:J{n + 200}", '"Compound,Isolation"'),
        (f"G2:G{n + 200}", '"None,Dumbbell,Barbell,EZ-Bar,Trap Bar,Kettlebell,Cable,Machine,Smith Machine,Leg Press,Hack Squat,Hammer Strength,Landmine,Medicine Ball,Plate"'),
        (f"B2:B{n + 200}", '"TRUE,FALSE"'),
    ]
    for ref, formula in dvs:
        dv = DataValidation(type="list", formula1=formula, allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(ref)
    style_header(ws, {"A": 38, "B": 8, "C": 8, "D": 13, "E": 26, "F": 28, "G": 13, "H": 10, "I": 11, "J": 11,
                      "K": 8, "L": 8, "M": 6, "N": 8, "O": 9, "P": 7, "Q": 70})

    # --- Equipment ---
    eq = wb.create_sheet("Equipment")
    eq.append(["Location", "Equipment", "Available", "Loading", "Bar kg", "Fixed weights", "Stack min", "Stack max", "Stack step", "Notes"])
    for name in ALL_EQUIPMENT:
        loading = GYM_LOADING.get(name, ("None", "", "", "", "", "", ""))
        eq.append(["Gym", name, True, loading[0], loading[1], loading[2], loading[3], loading[4], loading[5], loading[6]])
    for name in ALL_EQUIPMENT:
        if name == "Dumbbell":
            eq.append(["Home", name, True, "Plates", 2.5, "", "", "", "", "2 halterstangen van 2,5 kg; schijven: zie tab Plates."])
        else:
            loading = GYM_LOADING.get(name, ("None", "", "", "", "", "", ""))
            eq.append(["Home", name, name in HOME_AVAILABLE, loading[0], loading[1], loading[2], loading[3], loading[4], loading[5],
                       "Zet Available op TRUE als je dit thuis hebt." if name not in HOME_AVAILABLE else ""])
    dv = DataValidation(type="list", formula1='"None,Fixed,Plates,Stack"', allow_blank=True)
    eq.add_data_validation(dv)
    dv.add("D2:D400")
    dv = DataValidation(type="list", formula1='"TRUE,FALSE"', allow_blank=True)
    eq.add_data_validation(dv)
    dv.add("C2:C400")
    style_header(eq, {"A": 10, "B": 17, "C": 10, "D": 9, "E": 7, "F": 52, "G": 10, "H": 10, "I": 10, "J": 55})

    # --- Plates ---
    pl = wb.create_sheet("Plates")
    pl.append(["Location", "Equipment", "Plate kg", "Quantity", "Notes"])
    for kg, q in ((1, 4), (2, 4), (4, 4)):
        pl.append(["Home", "Dumbbell", kg, q, "Totaal aantal schijven (voor beide halters samen)."])
    for kg in (1.25, 2.5, 5, 10, 15, 20, 25):
        pl.append(["Gym", "*", kg, 10, "* = voor alle toestellen met Loading 'Plates' in de fitness."])
    style_header(pl, {"A": 10, "B": 12, "C": 9, "D": 9, "E": 60})

    # --- Muscles ---
    mu = wb.create_sheet("Muscles")
    mu.append(["Muscle", "Day", "Weekly sets", "Priority"])
    for m in MUSCLES:
        mu.append(list(m))
    style_header(mu, {"A": 14, "B": 10, "C": 12, "D": 9})

    # --- Settings ---
    st = wb.create_sheet("Settings")
    st.append(["Key", "Value", "Description"])
    for s in SETTINGS:
        st.append(list(s))
    style_header(st, {"A": 22, "B": 20, "C": 80})

    # --- Help ---
    hp = wb.create_sheet("Uitleg")
    for line in [
        ["FitTrick Library — uitleg"],
        [""],
        ["Exercises", "Eén rij per oefening. Active=FALSE haalt een oefening uit de voorstellen. Day wordt berekend uit Primary (tab Muscles)."],
        ["", "Equipment: alles wat nodig is (gescheiden door ;). Een oefening wordt alleen voorgesteld op een locatie waar al dat materiaal Available is."],
        ["", "Load: het materiaal waarvan je het gewicht ingeeft. Implements: 2 = twee halters tegelijk (gewicht per halter)."],
        ["", "Type: Weighted / Bodyweight / Timed (RepMin-RepMax = seconden) / Cardio (RepMin-RepMax = minuten)."],
        ["", "RestSec = rust tussen sets, SecPerRep = tempo; samen bepalen ze de geschatte duur."],
        ["Equipment", "Per locatie: welk materiaal er is en welke gewichten mogelijk zijn."],
        ["", "Loading Fixed = lijst vaste gewichten; Stack = van min tot max per stap; Plates = stang (Bar kg) + schijven uit tab Plates; None = geen gewicht."],
        ["Plates", "Schijven per locatie en toestel (* = alle toestellen met Plates). Bij halters: het totaal voor beide halters."],
        ["Muscles", "Spiergroep -> dag in het schema, gewenst aantal sets per week en prioriteit."],
        ["Settings", "Algemene instellingen."],
        [""],
        ["Na een wijziging: tik in de app op Instellingen > Opslaan & synchroniseren (of herstart de app)."],
    ]:
        hp.append(line)
    hp["A1"].font = Font(bold=True, size=14)
    hp.column_dimensions["A"].width = 14
    hp.column_dimensions["B"].width = 130
    wb.move_sheet("Uitleg", offset=-5)

    out = ROOT / "sheets" / "FitTrick Library.xlsx"
    wb.save(out)
    return out


def read_history():
    with open(HISTORY_CSV, encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def build_log(rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "Log"
    ws.append(["Date", "Exercise", "Reps", "Weight(kg)", "Duration(s)", "Distance(m)", "Incline", "Resistance",
               "isWarmup", "Note", "multiplier", "Workout ID", "Location", "Day"])
    for r in rows:
        ws.append([r["Date"], r["Exercise"], num(r["Reps"].strip()), num(r["Weight(kg)"]), num(r["Duration(s)"]),
                   round(float(r["Distance(m)"] or 0), 1), num(r["Incline"]), num(r["Resistance"]),
                   r["isWarmup"], r["Note"], num(r["multiplier"].strip()), "", "", ""])
    for c in ws["A"][1:]:
        c.number_format = "@"
    style_header(ws, {"A": 26, "B": 38, "C": 6, "D": 10, "E": 11, "F": 11, "K": 10, "L": 14, "M": 10, "N": 8})
    out = ROOT / "sheets" / f"FitTrick Log {USER}.xlsx"
    wb.save(out)
    return out


def parse_date(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S %z")


def build_dev(meta, rows):
    """Same JSON shapes as the Apps Script bootstrap response."""
    def table(header, data):
        return [dict(zip(header, d)) for d in data]

    lib = {
        "exercises": [{**{k: num(v) if k in ("Implements", "RepMin", "RepMax", "Sets", "RestSec", "SecPerRep") else v for k, v in r.items()}, "Active": True} for r in meta],
        "equipment": [], "plates": [],
        "muscles": table(["Muscle", "Day", "Weekly sets", "Priority"], MUSCLES),
        "settings": table(["Key", "Value", "Description"], SETTINGS),
    }
    hdr = ["Location", "Equipment", "Available", "Loading", "Bar kg", "Fixed weights", "Stack min", "Stack max", "Stack step"]
    for loc in ("Gym", "Home"):
        for name in ALL_EQUIPMENT:
            l = GYM_LOADING.get(name, ("None", "", "", "", "", "", ""))
            if loc == "Home" and name == "Dumbbell":
                l = ("Plates", 2.5, "", "", "", "", "")
            avail = True if loc == "Gym" else name in HOME_AVAILABLE
            lib["equipment"].append(dict(zip(hdr, [loc, name, avail, *l[:6]])))
    lib["plates"] = [{"Location": "Home", "Equipment": "Dumbbell", "Plate kg": k, "Quantity": 4} for k in (1, 2, 4)] + \
                    [{"Location": "Gym", "Equipment": "*", "Plate kg": k, "Quantity": 10} for k in (1.25, 2.5, 5, 10, 15, 20, 25)]

    now = max(parse_date(r["Date"]) for r in rows)
    cutoff = now - timedelta(days=70)
    ex, recent = {}, []
    for r in rows:
        d = parse_date(r["Date"])
        t = int(d.timestamp() * 1000)
        key = str(t)
        s = [num(r["Reps"].strip()), num(r["Weight(kg)"]), num(r["Duration(s)"]), round(float(r["Distance(m)"] or 0), 1),
             1 if r["isWarmup"] == "true" else 0]
        e = ex.setdefault(r["Exercise"], {"n": 0, "last": 0, "sets": []})
        e["n"] += 1
        if t > e["last"]:
            e["last"], e["sets"] = t, [s]
        elif t == e["last"]:
            e["sets"].append(s)
        if d >= cutoff:
            recent.append([t, r["Exercise"], *s, num(r["multiplier"].strip()), key, "Gym", ""])
    (ROOT / "dev-data" / "library.json").write_text(json.dumps(lib), encoding="utf-8")
    (ROOT / "dev-data" / "history.json").write_text(json.dumps({"exercises": ex, "recent": recent}), encoding="utf-8")


def main():
    meta = read_meta()
    rows = read_history()
    names = {r["Exercise"] for r in meta}
    missing = sorted({r["Exercise"] for r in rows} - names)
    if missing:
        print("WAARSCHUWING: oefeningen uit de historiek zonder metadata:", missing)
    print(build_library(meta))
    print(build_log(rows))
    build_dev(meta, rows)
    print("dev-data ok;", len(meta), "oefeningen,", len(rows), "logrijen")


if __name__ == "__main__":
    main()
