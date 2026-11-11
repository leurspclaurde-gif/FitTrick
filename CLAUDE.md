# FitTrick — project context for Claude

Personal workout-guidance app for **Patrick** (Dutch-speaking; talk to him in Dutch, keep exercise names in English).
Runs as a PWA on his **iPhone**; data lives in **Google Sheets on his private Google account**.

- Live app: https://leurspclaurde-gif.github.io/FitTrick/
- Repo: https://github.com/leurspclaurde-gif/FitTrick (public, branch `main`, GitHub user `leurspclaurde-gif`, commits use `leurspclaurde-gif@users.noreply.github.com`)
- Setup/user docs: `SETUP.md` (short) and `docs/FitTrick Handleiding.docx` (full manual, uploaded by Patrick to his Drive as a Google Doc)

## Session ritual: "sluit af"
When Patrick says **"sluit af"** (or `/sluit-af`) while working on FitTrick, run the `sluit-af` skill (`.claude/skills/sluit-af/SKILL.md`): update this file (status, decisions, backlog, session log), check the manual for outdated parts, and report what is uncommitted.

## Requirements (from Patrick)
- Train ~5×/week, **PPL rotation that simply continues** (rest days don't shift it). Also "Full Body" and a custom muscle-group focus.
- Proposals choose muscles, exercises, sets, reps and weight; **everything editable**. Take into account that all muscles get trained and what was done recently.
- Proposal fits a **target duration**, adjustable in **15-minute steps**, using exercise time + rest.
- **Every workout ends with ≥1 ab/core exercise.**
- **Locations**: Gym (lots of equipment) and Home (2 dumbbell handles 2.5 kg, plates 4×1, 4×2, 4×4 kg, a mat). Equipment is in the Library sheet so new gear unlocks exercises; available weights per equipment (e.g. fixed dumbbells / EZ bars).
- Library viewable/editable in Google Sheet **`FitTrick Library`**; every workout logged to **`FitTrick Log <User>`** (`FitTrick Log Patrick`).
- Cardio (mostly walking) can be logged manually.
- App starts with the splash image (`app/img/splash.webp`), tap → home.
- Single user for now (but user name is a setting).

## Architecture
```
iPhone PWA (app/, vanilla JS, no build)  ⇄  Apps Script web app (apps-script/Code.gs, bound to FitTrick Library)  ⇄  Google Sheets
```
- **No build step.** Plain ES modules served as static files by GitHub Pages (`.github/workflows/pages.yml` deploys the `app/` folder on push to `main` touching `app/**`).
- **API**: all calls are `POST` with `Content-Type: text/plain` (avoids CORS preflight) to the `/exec` URL, body `{action, token, user, ...}`.
  - `bootstrap` → `{library:{exercises,equipment,plates,muscles,settings}, history:{exercises:{name:{n,last,sets:[[reps,w,dur,dist,warm]]}}, recent:[[t,name,reps,w,dur,dist,warm,mult,key,loc,day]]}}` (recent = last 70 days).
  - `log` → appends `workout.rows`; idempotent on `Workout ID` (checks last 400 rows).
  - Token in Script Properties `TOKEN` (created by `setup()`); log sheet id cached as `LOG_ID_<user>`; log found by exact name in Drive or created.
- **Offline**: finished workouts go to `ft.outbox` + `ft.local` in localStorage, sent when possible; `mergedHistory()` merges unsent ones. Active workout persisted in `ft.plan` (survives the app being killed). Service worker `app/sw.js` = network-first with cache fallback.

### Files
| Path | Role |
|---|---|
| `app/js/main.js` | UI: views (splash, home, plan, workout, summary, cardio, history, settings), modals (swap/add/focus), actions, rest timer (WebAudio beep), wake lock. Renders HTML strings; event delegation via `data-a` (click) and `data-in` (change). |
| `app/js/planner.js` | Pure logic: `normalizeLibrary`, `sessions`, `nextDay`, `muscleVolume`, `prescribe` (progression), `itemSeconds`, `propose`, `alternatives`. |
| `app/js/weights.js` | `loadOptions(lib, location, load, impl)` → available loads (Fixed / Stack / Plates), `nearest`, `stepWeight`. |
| `app/js/data.js` | localStorage, `sync()`, `logWorkout()`, `flushOutbox()`, dev mode. |
| `app/sw.js` | Offline cache — **bump `VERSION` on every app release**. |
| `apps-script/Code.gs` | Backend. After changes Patrick must redeploy: *Implementeren → Implementaties beheren → ✎ → Nieuwe versie* (keeps URL). |
| `tools/classify_exercises.py` | Hand-written metadata for every exercise → `tools/exercise_meta.csv` (gitignored). |
| `tools/build_sheets.py` | Builds `sheets/FitTrick Library.xlsx`, `sheets/FitTrick Log Patrick.xlsx` and `dev-data/*.json` from the Fitbod CSV + meta. Only for the initial import — after that the Google Sheets are the source of truth (Patrick edits them). |
| `tests/planner.test.mjs` | `node --test tests/` (needs `dev-data/`). |
| `docs/` | Manual (docx) + its generator. |

### Sheet structure (FitTrick Library)
- **Exercises**: Exercise, Active, Day (formula from Muscles), Primary, Secondary (`;`), Equipment (`;`, all required), Load (item whose weight is entered), Implements (2 = two dumbbells, weight is per dumbbell), Type (Weighted/Bodyweight/Timed/Cardio), Mechanics, RepMin, RepMax (seconds for Timed, minutes for Cardio), Sets, RestSec, SecPerRep, Added, Instructions.
- **Equipment**: Location, Equipment, Available, Loading (None/Fixed/Plates/Stack), Bar kg, Fixed weights, Stack min/max/step, Notes. An exercise is eligible at a location when all its Equipment is Available there (`Bodyweight` is implicit).
- **Plates**: Location, Equipment (`*` = all plate-loaded at that location), Plate kg, Quantity (total for both implements).
- **Muscles**: Muscle, Day (Push/Pull/Legs/Core/Cardio/Mobility), Weekly sets, Priority. Muscle order = ordering inside a workout.
- **Settings**: User, PPL Order, Default minutes, Duration step, Transition sec, Min core exercises, Weekly window days, Variety sessions.
- **Log** (`FitTrick Log Patrick`): Fitbod-compatible columns `Date, Exercise, Reps, Weight(kg), Duration(s), Distance(m), Incline, Resistance, isWarmup, Note, multiplier` + `Workout ID, Location, Day`. Date stored as text `yyyy-MM-dd HH:mm:ss +0000` (UTC). Contains full Fitbod history since 2023-10.

### Planner (how proposals work)
1. Day = `nextDay` (last strength session's day → next in PPL Order) unless chosen.
2. Need per muscle = (weekly target − sets in last 7 days, ≥0) + 30 % of target, × priority.
3. Core finisher reserved first (variety over last 4 sessions), then greedy pick of main exercises: score = need(primary) + 0.3·need(secondaries) × familiarity (log of sets logged) × variety (penalty if used in last 2 same-day sessions) × compound bonus (first slots) × seeded jitter. Max 2 per primary muscle (relaxed to 3 if time is left). After each pick need(primary) ×0.45, need(secondary) ×0.8. Stop when the time budget is used; spare time → extra core (max 3).
4. Order: compounds first, then by Muscles-tab order, weighted before bodyweight; core last.
5. `prescribe`: last working sets → if min reps at top weight ≥ RepMax → next available load above last weight, reps = RepMin; else same (rounded) weight, reps +1. Timed: +5 s. No history → weight empty ("kies je gewicht").
6. Time per exercise = sets × reps × SecPerRep + (sets−1) × RestSec + Transition sec.

## Development
```bash
python -I tools/build_sheets.py   # regenerate xlsx + dev-data (needs the Fitbod CSV, local only)
node --test tests/                # planner tests
```
Local preview: `.claude/launch.json` → server `fittrick` (python http.server 8321 at project root) → open `http://localhost:8321/app/?dev` (uses `dev-data/`, no Google needed; logged workouts go to localStorage `ft.devhist`). Test at mobile viewport (375×812). Browser caches CSS — reload with a cache-buster if styles look stale.

Release: change app → bump `VERSION` in `app/sw.js` → run tests → commit → push to `main` → GitHub Action deploys (~1 min). iPhone picks it up on next open (sometimes needs the app closed and reopened twice).

## Gotchas
- `implements` is a reserved word in ES modules — don't use it as a variable/parameter name (property access `e.implements` is fine).
- Gym machine/cable weights in the Fitbod history are often lb conversions (41, 52, 59 kg…); Equipment tab uses 2.5 kg stacks — Patrick may adjust per machine.
- iOS: no `navigator.vibrate`; audio only after a user gesture (`unlockAudio` on taps); Wake Lock may not work in every iOS version; the home-screen app has separate storage from Safari.
- **Privacy**: repo is public. Never commit `*.csv`, `sheets/`, `dev-data/`, tokens or the Apps Script URL (`.gitignore` covers files). Never use the work (Prato) Google/Atlassian connectors for FitTrick — Patrick's data lives on his private Google account; give him files to upload instead.

## Status
- v1.0 live and working on Patrick's iPhone (confirmed 2026-11-11).
- Not verified on device by Claude: rest-timer sound, wake lock.

## Backlog / ideas
- Progress charts per exercise (PR's, estimated 1RM) in the app.
- Warm-up sets for heavy compounds (Patrick: not needed for now).
- Apple Health / Shortcut integration for walking.
- Exercise library browser in the app; per-machine weight steps.
- Multi-user (setting `User` already drives the log name).

## Session log
- **2026-11-11** — Built v1: PWA, planner, Apps Script backend, Library (614 exercises: 554 from Fitbod history + 60 added, mainly home), Log with full history, GitHub Pages deploy (actions bumped to Node 24 versions), CLAUDE.md, `sluit-af` skill, Handleiding.
