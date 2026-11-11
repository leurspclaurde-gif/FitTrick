# FitTrick — installatie

Drie stappen: **(A)** Google Sheets + Apps Script in je privé Google-account, **(B)** de app online zetten via GitHub Pages, **(C)** de app op je iPhone installeren.

```
iPhone (FitTrick-app)  ⇄  Apps Script (web app)  ⇄  Google Sheets
                                                     ├─ FitTrick Library      (oefeningen, materiaal, instellingen)
                                                     └─ FitTrick Log Patrick  (elke set van elke training)
```

---

## A. Google Sheets en Apps Script (privé-account)

1. Ga naar **drive.google.com** en controleer rechtsboven dat je met je **privé-account** aangemeld bent.
2. Tandwiel ⚙ → **Instellingen** → vink **"Geüploade bestanden converteren naar de Google Documenten-editorindeling"** aan.
3. Sleep deze twee bestanden in Drive:
   - `sheets\FitTrick Library.xlsx`
   - `sheets\FitTrick Log Patrick.xlsx`

   Controleer daarna de namen: ze moeten exact **`FitTrick Library`** en **`FitTrick Log Patrick`** heten (zonder `.xlsx`). Hernoem ze zo nodig.
4. Open **FitTrick Library** → menu **Extensies → Apps Script**.
   - Geef het project de naam `FitTrick` (links bovenaan).
   - Vervang alle code in `Code.gs` door de inhoud van `apps-script\Code.gs` en klik op 💾 **Opslaan**.
5. Kies bovenaan de functie **`setup`** en klik op **▶ Uitvoeren**.
   - Google vraagt toestemming. Je krijgt een waarschuwing "Google heeft deze app niet geverifieerd": klik op **Geavanceerd → Ga naar FitTrick (onveilig)** → **Toestaan**. Het is je eigen script, dus dit is normaal.
   - In het **uitvoeringslogboek** zie je je **token** en de gevonden log-sheet (met ongeveer 19.762 rijen historiek). Noteer de token.
6. Klik rechtsboven op **Implementeren → Nieuwe implementatie**.
   - Type: ⚙ → **Web-app**.
   - Uitvoeren als: **Ik**. Wie heeft toegang: **Iedereen**.
   - Klik op **Implementeren** en kopieer de **URL van de web-app** (eindigt op `/exec`).

   "Iedereen" betekent dat het adres bereikbaar is, maar zonder je token krijgt niemand gegevens te zien of kan niemand iets loggen.

> **Code.gs later aanpassen?** Kies **Implementeren → Implementaties beheren → ✎ → Versie: Nieuwe versie**. Zo blijft de URL dezelfde.

---

## B. De app online zetten (GitHub Pages, gratis)

Je iPhone kan een web-app alleen installeren als die via **https** online staat. GitHub Pages doet dat gratis.

1. Maak een account aan op **github.com/signup**. Dat doe je zelf: het is jouw account.
2. Maak een nieuwe repository: **+ → New repository**.
   - Naam: `fittrick`.
   - Kies **Public**. Met een gratis account werkt Pages alleen voor publieke repositories.
   - Vink niets anders aan en klik op **Create repository**.
3. Laat Claude de code pushen. Geef daarvoor je GitHub-gebruikersnaam door. De eerste keer opent er een browservenster om aan te melden bij GitHub.
4. Ga in de repository naar **Settings → Pages** en zet **Source** op **GitHub Actions**.
5. Na ongeveer een minuut staat de app op **`https://<gebruikersnaam>.github.io/fittrick/`**. De voortgang zie je onder het tabblad **Actions**.

**Wat is er publiek?** Alleen de app-code en het startscherm. Je trainingsdata, je CSV, de spreadsheets, de Apps Script-URL en je token staan **niet** in de repository: `.gitignore` houdt die buiten.

---

## C. Installeren op je iPhone

1. Open **Safari** (niet Chrome) en ga naar `https://<gebruikersnaam>.github.io/fittrick/`.
2. Tik op **Deel** (vierkant met pijl) → **Zet op beginscherm** → **Voeg toe**.
3. Open FitTrick vanaf je beginscherm, tik op het startscherm en ga naar **⚙ Instellingen**:
   - Gebruiker: `Patrick`
   - Apps Script-URL: de `/exec`-URL uit stap A6
   - Token: uit stap A5

   Tik daarna op **Opslaan & synchroniseren**.

Doe dit in de app op je beginscherm, niet in Safari: iOS bewaart hun gegevens apart.

---

## Dagelijks gebruik

- **Training**: kies de locatie (Fitness of Thuis), het schema (de app stelt de volgende PPL-dag voor) en de duur (per 15 minuten aan te passen). Tik daarna op **Stel training voor**. Alles is aanpasbaar: ⇄ wisselen, ✎ sets/herhalingen/gewicht, ↑↓ volgorde, ✕ verwijderen, + toevoegen, *Spiergroepen*, 🎲 *Ander voorstel*.
- **Tijdens de training**: vink elke set af ✓. De rusttimer start dan automatisch, met een geluid aan het einde. Elke training eindigt met minstens één buikspieroefening.
- **Opslaan**: na *Afronden → Opslaan in log* komt elke set in `FitTrick Log Patrick`. Zonder netwerk wordt de training op je iPhone bewaard en later automatisch verstuurd.
- **Cardio/wandelen**: kies **🚶 Cardio loggen** op het hoofdscherm.
- **Bibliotheek aanpassen**: wijzig `FitTrick Library` in Google Sheets. Uitleg per kolom staat op het tabblad *Uitleg*. Nieuw materiaal thuis? Zet het tabblad *Equipment* → `Home` → *Available* op TRUE (en voeg gewichten of schijven toe). De app synchroniseert bij het opstarten, of via Instellingen.

---

## Voor ontwikkeling (pc)

```bash
python -I tools/build_sheets.py      # bouwt sheets/*.xlsx en dev-data/*.json uit de CSV
node --test tests/                   # test de voorstel-logica
python -m http.server 8321           # daarna http://localhost:8321/app/?dev  (testdata, geen Google nodig)
```
Verhoog na een wijziging aan de app `VERSION` in `app/sw.js`, zodat je iPhone de nieuwe versie ophaalt.
