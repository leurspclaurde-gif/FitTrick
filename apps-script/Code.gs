/**
 * FitTrick backend — Google Apps Script, bound to the "FitTrick Library" spreadsheet.
 *
 * The FitTrick app (PWA) talks to this script as a web app:
 *   POST {action:"bootstrap", token, user}         -> library + training history summary
 *   POST {action:"log", token, user, workout:{..}}  -> appends the sets to "FitTrick Log <user>"
 *
 * Setup: see SETUP.md. Run setup() once from the editor, then Deploy > New deployment > Web app
 * (Execute as: Me, Who has access: Anyone).
 */

var LOG_HEADERS = ['Date', 'Exercise', 'Reps', 'Weight(kg)', 'Duration(s)', 'Distance(m)', 'Incline',
  'Resistance', 'isWarmup', 'Note', 'multiplier', 'Workout ID', 'Location', 'Day'];
var RECENT_DAYS = 70;

/** Run once from the Apps Script editor. Creates the secret token and checks the log sheet. */
function setup() {
  var props = PropertiesService.getScriptProperties();
  var token = props.getProperty('TOKEN');
  if (!token) {
    token = Utilities.getUuid().replace(/-/g, '').slice(0, 20);
    props.setProperty('TOKEN', token);
  }
  var ss = SpreadsheetApp.getActive();
  ['Exercises', 'Equipment', 'Plates', 'Muscles', 'Settings'].forEach(function (name) {
    if (!ss.getSheetByName(name)) throw new Error('Tab "' + name + '" ontbreekt in deze spreadsheet.');
  });
  var user = getSetting_('User') || 'Patrick';
  var log = getLogSheet_(user, true);
  Logger.log('Token (vul in in de app bij Instellingen): ' + token);
  Logger.log('Log-sheet: ' + log.getParent().getName() + ' (' + (log.getLastRow() - 1) + ' rijen) ' + log.getParent().getUrl());
}

function doGet() {
  return json_({ ok: true, app: 'FitTrick', hint: 'Use POST' });
}

function doPost(e) {
  try {
    var req = JSON.parse(e.postData.contents);
    var token = PropertiesService.getScriptProperties().getProperty('TOKEN');
    if (!token || req.token !== token) return json_({ ok: false, error: 'Ongeldige token' });
    var user = String(req.user || '').trim();
    if (!/^[\w \-]{1,40}$/.test(user)) return json_({ ok: false, error: 'Ongeldige gebruikersnaam' });

    if (req.action === 'bootstrap') {
      return json_({ ok: true, library: readLibrary_(), history: readHistory_(user), serverTime: new Date().toISOString() });
    }
    if (req.action === 'log') {
      return json_(appendWorkout_(user, req.workout));
    }
    return json_({ ok: false, error: 'Onbekende actie' });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  }
}

/* ---------- library ---------- */

function readLibrary_() {
  var ss = SpreadsheetApp.getActive();
  return {
    exercises: readTable_(ss.getSheetByName('Exercises')),
    equipment: readTable_(ss.getSheetByName('Equipment')),
    plates: readTable_(ss.getSheetByName('Plates')),
    muscles: readTable_(ss.getSheetByName('Muscles')),
    settings: readTable_(ss.getSheetByName('Settings'))
  };
}

function readTable_(sheet) {
  var values = sheet.getDataRange().getValues();
  var headers = values.shift().map(function (h) { return String(h).trim(); });
  return values.filter(function (r) { return String(r[0]).trim() !== ''; }).map(function (r) {
    var o = {};
    headers.forEach(function (h, i) { if (h) o[h] = r[i] instanceof Date ? r[i].toISOString() : r[i]; });
    return o;
  });
}

function getSetting_(key) {
  var sh = SpreadsheetApp.getActive().getSheetByName('Settings');
  if (!sh) return null;
  var rows = sh.getDataRange().getValues();
  for (var i = 1; i < rows.length; i++) if (String(rows[i][0]).trim() === key) return String(rows[i][1]).trim();
  return null;
}

/* ---------- log sheet ---------- */

function getLogSheet_(user, create) {
  var props = PropertiesService.getScriptProperties();
  var key = 'LOG_ID_' + user;
  var id = props.getProperty(key);
  var ss = null;
  if (id) { try { ss = SpreadsheetApp.openById(id); } catch (e) { ss = null; } }
  if (!ss) {
    var name = 'FitTrick Log ' + user;
    var files = DriveApp.getFilesByName(name);
    while (files.hasNext()) {
      var f = files.next();
      if (f.getMimeType() === MimeType.GOOGLE_SHEETS && !f.isTrashed()) { ss = SpreadsheetApp.open(f); break; }
    }
    if (!ss) {
      if (!create) throw new Error('Log-sheet "' + name + '" niet gevonden in Google Drive.');
      ss = SpreadsheetApp.create(name);
    }
    props.setProperty(key, ss.getId());
  }
  var sheet = ss.getSheets()[0];
  var lastCol = Math.max(sheet.getLastColumn(), 1);
  var header = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(String);
  if (header[0] !== 'Date') {
    sheet.getRange(1, 1, 1, LOG_HEADERS.length).setValues([LOG_HEADERS]).setFontWeight('bold');
    sheet.setFrozenRows(1);
  } else if (header.length < LOG_HEADERS.length || header[LOG_HEADERS.length - 1] !== 'Day') {
    sheet.getRange(1, 1, 1, LOG_HEADERS.length).setValues([LOG_HEADERS]).setFontWeight('bold');
  }
  return sheet;
}

function appendWorkout_(user, w) {
  if (!w || !w.id || !w.rows || !w.rows.length) return { ok: false, error: 'Lege training' };
  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sheet = getLogSheet_(user, true);
    var last = sheet.getLastRow();
    // Idempotency: the app retries when offline; skip a workout that is already logged.
    if (last > 1) {
      var from = Math.max(2, last - 400);
      var ids = sheet.getRange(from, 12, last - from + 1, 1).getValues();
      for (var i = 0; i < ids.length; i++) if (ids[i][0] === w.id) return { ok: true, duplicate: true };
    }
    var date = formatDate_(new Date(w.date || Date.now()));
    var out = w.rows.map(function (r) {
      return [date, r.exercise, num_(r.reps), num_(r.weight), num_(r.duration), num_(r.distance), 0, 0,
        r.warmup ? 'true' : 'false', r.note || '', num_(r.multiplier), w.id, w.location || '', w.day || ''];
    });
    var range = sheet.getRange(last + 1, 1, out.length, LOG_HEADERS.length);
    sheet.getRange(last + 1, 1, out.length, 1).setNumberFormat('@'); // keep the date as text
    range.setValues(out);
    return { ok: true, rows: out.length };
  } finally {
    lock.releaseLock();
  }
}

/* ---------- history summary ---------- */

function readHistory_(user) {
  var sheet;
  try { sheet = getLogSheet_(user, false); } catch (e) { return { exercises: {}, recent: [] }; }
  var last = sheet.getLastRow();
  if (last < 2) return { exercises: {}, recent: [] };
  var values = sheet.getRange(2, 1, last - 1, LOG_HEADERS.length).getValues();
  var cutoff = Date.now() - RECENT_DAYS * 864e5;
  var ex = {};      // exercise -> {n, last, sets}
  var recent = [];  // compact rows of the last RECENT_DAYS days
  values.forEach(function (r) {
    var d = parseDate_(r[0]);
    if (!d) return;
    var name = String(r[1]);
    var t = d.getTime();
    var key = r[11] ? String(r[11]) : String(t);
    var set = [num_(r[2]), num_(r[3]), num_(r[4]), num_(r[5]), String(r[8]) === 'true' ? 1 : 0];
    var s = ex[name];
    if (!s) s = ex[name] = { n: 0, last: 0, key: '', sets: [] };
    s.n++;
    if (t > s.last || (t === s.last && key === s.key)) {
      if (key !== s.key) { s.last = t; s.key = key; s.sets = []; }
      s.sets.push(set);
    }
    if (t >= cutoff) recent.push([t, name, set[0], set[1], set[2], set[3], set[4], num_(r[10]), key, String(r[12] || ''), String(r[13] || '')]);
  });
  Object.keys(ex).forEach(function (k) { delete ex[k].key; });
  return { exercises: ex, recent: recent };
}

/* ---------- helpers ---------- */

function parseDate_(v) {
  if (v instanceof Date) return v;
  var s = String(v).trim();
  if (!s) return null;
  // "2026-11-11 07:20:05 +0000"
  var m = s.match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})\s*([+-]\d{2}):?(\d{2})?$/);
  var d = m ? new Date(m[1] + 'T' + m[2] + m[3] + ':' + (m[4] || '00')) : new Date(s);
  return isNaN(d.getTime()) ? null : d;
}

function formatDate_(d) {
  return Utilities.formatDate(d, 'UTC', "yyyy-MM-dd HH:mm:ss '+0000'");
}

function num_(v) {
  var n = Number(v);
  return isFinite(n) ? n : 0;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
