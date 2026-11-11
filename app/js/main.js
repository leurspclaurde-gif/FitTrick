import { normalizeLibrary, propose, prescribe, alternatives, sessions, nextDay, itemSeconds, planSeconds,
  musclesOfDay, eligible, dayOf, fmtKg, DAY_TYPES } from './planner.js';
import { loadOptions, stepWeight, nearest } from './weights.js';
import { store, sync, mergedHistory, logWorkout, flushOutbox, save } from './data.js';

const $app = document.getElementById('app');
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const mmss = s => { s = Math.max(0, Math.round(s)); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`; };
const mins = s => Math.round(s / 60);
const hasWeight = e => !!e && (e.type === 'Weighted' || (e.type === 'Timed' && e.load !== 'None'));
const kg = w => (w == null ? '–' : (Math.round(w * 100) / 100).toString().replace('.', ','));

const S = { view: 'splash', modal: null, msg: '', busy: false, lib: null, hist: null, expanded: null };

/* ---------------- boot ---------------- */

function loadLib() {
  const raw = store.rawLib();
  S.lib = raw ? normalizeLibrary(raw) : null;
  S.hist = mergedHistory();
}

async function doSync(silent) {
  S.busy = true; if (!silent) render();
  try {
    await sync();
    loadLib();
    S.msg = '';
  } catch (e) {
    S.msg = e.message;
  }
  S.busy = false;
  render();
}

function plan() { return store.plan(); }
function setPlan(p) { store.setPlan(p); render(); }

/* ---------------- audio / wake lock ---------------- */

let audio;
function unlockAudio() {
  try { audio = audio || new (window.AudioContext || window.webkitAudioContext)(); if (audio.state === 'suspended') audio.resume(); } catch {}
}
function beep(times = 3) {
  if (!audio) return;
  for (let i = 0; i < times; i++) {
    const o = audio.createOscillator(), g = audio.createGain();
    o.frequency.value = 880; o.connect(g); g.connect(audio.destination);
    const t = audio.currentTime + i * 0.35;
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.4, t + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.25);
    o.start(t); o.stop(t + 0.3);
  }
  navigator.vibrate?.([200, 100, 200]);
}
let wakeLock = null;
async function keepAwake(on) {
  try {
    if (on && !wakeLock && 'wakeLock' in navigator) { wakeLock = await navigator.wakeLock.request('screen'); wakeLock.addEventListener('release', () => { wakeLock = null; }); }
    if (!on && wakeLock) { await wakeLock.release(); wakeLock = null; }
  } catch {}
}
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible' && S.view === 'workout') keepAwake(true); });

/* ---------------- helpers ---------------- */

const cfg = () => store.cfg();
const ex = name => S.lib?.byName.get(name);
const locs = () => (S.lib?.locations.length ? S.lib.locations : ['Gym', 'Home']);
const locLabel = l => ({ Gym: 'Fitness', Home: 'Thuis' }[l] || l);
const dayLabel = d => ({ 'Full Body': 'Full body', Cardio: 'Cardio', Other: 'Overig' }[d] || d);

function currentLocation() { const c = cfg(); return locs().includes(c.location) ? c.location : locs()[0]; }
function currentMinutes() { return cfg().minutes || S.lib?.settings.minutes || 60; }
function setCfg(patch) { store.setCfg({ ...cfg(), ...patch }); }

function optionsFor(p, name) { const e = ex(name); return e ? loadOptions(S.lib, p.location, e.load, e.implements) : null; }

function setLine(e, s) {
  if (!e) return '';
  if (e.type === 'Cardio') return `${mins(s.duration)} min${s.distance ? ' · ' + kg(s.distance / 1000) + ' km' : ''}`;
  if (e.type === 'Timed') return `${s.duration}s${hasWeight(e) && s.weight ? ' @ ' + kg(s.weight) + ' kg' : ''}`;
  return `${s.reps}${e.type === 'Weighted' ? ' × ' + (s.weight == null ? '? kg' : kg(s.weight) + ' kg') : ''}`;
}
function itemSummary(it) {
  const e = ex(it.name);
  const first = it.sets[0];
  const same = it.sets.every(s => setLine(e, s) === setLine(e, first));
  return same ? `${it.sets.length} × ${setLine(e, first)}` : it.sets.map(s => setLine(e, s)).join(', ');
}

function newProposal(over = {}) {
  const prev = plan();
  const opts = {
    day: over.day ?? S.day ?? nextDay(S.lib, sessions(S.lib, S.hist)),
    location: over.location ?? currentLocation(),
    minutes: over.minutes ?? currentMinutes(),
    focus: over.focus ?? null,
    seed: over.seed ?? (prev?.status === 'proposal' ? prev.seed : Math.floor(Math.random() * 1e9)),
  };
  const p = propose(S.lib, S.hist, opts);
  setPlan({ id: crypto.randomUUID(), status: 'proposal', seed: opts.seed, customFocus: !!opts.focus, ...p });
  S.view = 'plan';
  render();
}

function sessionDate(t) {
  return new Date(t).toLocaleDateString('nl-BE', { weekday: 'short', day: 'numeric', month: 'short' });
}

/* ---------------- views ---------------- */

function vSplash() {
  return `<div class="splash" data-a="enter"><img src="img/splash.webp" alt="FitTrick"><div class="splash-hint">Tik om te starten</div></div>`;
}

function header(title, back = 'home', right = '') {
  return `<header class="bar">${back ? `<button class="icon" data-a="go" data-v="${back}" aria-label="Terug">‹</button>` : '<span class="icon"></span>'}
    <h1>${esc(title)}</h1>${right || '<span class="icon"></span>'}</header>`;
}

function vSetup() {
  return `${header('FitTrick', '', `<button class="icon" data-a="go" data-v="settings" aria-label="Instellingen">⚙︎</button>`)}
  <main><div class="card"><h2>Welkom 👋</h2>
  <p>De app is nog niet gekoppeld aan je Google Sheets. Vul bij <b>Instellingen</b> de Apps Script-URL en je token in (zie SETUP.md).</p>
  ${S.msg ? `<p class="err">${esc(S.msg)}</p>` : ''}
  <button class="btn primary" data-a="go" data-v="settings">Naar instellingen</button></div></main>`;
}

function vHome() {
  if (!S.lib) return vSetup();
  const p = plan();
  const sess = sessions(S.lib, S.hist);
  const next = nextDay(S.lib, sess);
  const day = S.day ?? next;
  const loc = currentLocation();
  const m = currentMinutes();
  const pending = store.outbox().length;
  const synced = store.syncedAt();
  return `${header('FitTrick', '', `<button class="icon" data-a="go" data-v="settings" aria-label="Instellingen">⚙︎</button>`)}
  <main>
    <p class="muted small">${S.busy ? 'Synchroniseren…' : synced ? 'Gesynchroniseerd ' + new Date(synced).toLocaleString('nl-BE', { dateStyle: 'short', timeStyle: 'short' }) : ''}
      ${pending ? ` · <b>${pending} training(en) wachten op verzending</b>` : ''}
      ${S.msg ? `<br><span class="${S.msg.includes('✓') ? 'ok' : 'err'}">${esc(S.msg)}</span>` : ''}</p>
    ${p && p.status === 'active' ? `<div class="card accent"><h2>Training bezig</h2><p>${esc(dayLabel(p.day))} · ${esc(locLabel(p.location))} · gestart ${new Date(p.startedAt).toLocaleTimeString('nl-BE', { timeStyle: 'short' })}</p>
      <button class="btn primary" data-a="go" data-v="workout">Hervatten</button></div>` : ''}
    ${p && p.status === 'proposal' ? `<div class="card"><p>Je hebt nog een voorstel klaarstaan (${esc(dayLabel(p.day))}).</p><button class="btn" data-a="go" data-v="plan">Bekijk voorstel</button></div>` : ''}
    <div class="card">
      <h2>Nieuwe training</h2>
      <label class="lbl">Locatie</label>
      <div class="seg">${locs().map(l => `<button class="${l === loc ? 'on' : ''}" data-a="loc" data-v="${esc(l)}">${esc(locLabel(l))}</button>`).join('')}</div>
      <label class="lbl">Schema</label>
      <div class="seg">${DAY_TYPES.map(d => `<button class="${d === day ? 'on' : ''}" data-a="day" data-v="${esc(d)}">${esc(dayLabel(d))}${d === next ? '<small>volgende</small>' : ''}</button>`).join('')}</div>
      <label class="lbl">Duur</label>
      <div class="stepper big"><button data-a="min" data-v="-1">−</button><span>${m} min</span><button data-a="min" data-v="1">+</button></div>
      <button class="btn primary" data-a="propose">Stel training voor</button>
    </div>
    <div class="row2">
      <button class="btn" data-a="go" data-v="cardio">🚶 Cardio loggen</button>
      <button class="btn" data-a="go" data-v="history">📅 Historiek</button>
    </div>
    <h3>Laatste trainingen</h3>
    ${sess.slice(0, 6).map(s => `<div class="li"><b>${esc(sessionDate(s.t))}</b> · ${esc(dayLabel(s.day))}<br><span class="muted small">${esc(s.items.map(i => i.name).join(', '))}</span></div>`).join('') || '<p class="muted">Nog geen trainingen.</p>'}
  </main>`;
}

function itemCard(p, it, i, editable) {
  const e = ex(it.name);
  const open = S.expanded === i;
  return `<div class="card item">
    <div class="item-head" data-a="expand" data-i="${i}">
      <div><b>${esc(it.name)}</b><div class="muted small">${esc(e?.primary || '?')}${e?.secondary.length ? ' · ' + esc(e.secondary.join(', ')) : ''}</div></div>
      <div class="right"><div>${esc(itemSummary(it))}</div><div class="muted small">≈ ${mins(itemSeconds(S.lib, it))} min</div></div>
    </div>
    ${it.note ? `<div class="note">${esc(it.note)}</div>` : ''}
    ${open ? setEditor(p, it, i, false) : ''}
    ${editable ? `<div class="actions">
      <button data-a="expand" data-i="${i}">✎ Aanpassen</button>
      <button data-a="swap" data-i="${i}">⇄ Wissel</button>
      <button data-a="up" data-i="${i}" ${i === 0 ? 'disabled' : ''}>↑</button>
      <button data-a="down" data-i="${i}" ${i === p.items.length - 1 ? 'disabled' : ''}>↓</button>
      <button data-a="remove" data-i="${i}" class="danger">✕</button></div>` : ''}
  </div>`;
}

function setEditor(p, it, i, live) {
  const e = ex(it.name);
  if (!e) return '';
  const opts = optionsFor(p, it.name);
  const rows = it.sets.map((s, j) => {
    const cells = [];
    if (hasWeight(e)) cells.push(`<div class="stepper"><button data-a="w" data-i="${i}" data-j="${j}" data-v="-1">−</button>
      <input inputmode="decimal" data-in="weight" data-i="${i}" data-j="${j}" value="${s.weight == null ? '' : kg(s.weight)}" placeholder="kg"><button data-a="w" data-i="${i}" data-j="${j}" data-v="1">+</button></div>`);
    if (e.type === 'Timed' || e.type === 'Cardio') {
      const unit = e.type === 'Cardio' ? 'min' : 's';
      const val = e.type === 'Cardio' ? mins(s.duration) : s.duration;
      cells.push(`<div class="stepper"><button data-a="d" data-i="${i}" data-j="${j}" data-v="-1">−</button>
        <input inputmode="numeric" data-in="duration" data-i="${i}" data-j="${j}" value="${val}"><span class="unit">${unit}</span><button data-a="d" data-i="${i}" data-j="${j}" data-v="1">+</button></div>`);
      if (e.type === 'Cardio') cells.push(`<div class="stepper"><input inputmode="decimal" data-in="distance" data-i="${i}" data-j="${j}" value="${s.distance ? kg(s.distance / 1000) : ''}" placeholder="km"><span class="unit">km</span></div>`);
    } else {
      cells.push(`<div class="stepper"><button data-a="r" data-i="${i}" data-j="${j}" data-v="-1">−</button>
        <input inputmode="numeric" data-in="reps" data-i="${i}" data-j="${j}" value="${s.reps}"><span class="unit">×</span><button data-a="r" data-i="${i}" data-j="${j}" data-v="1">+</button></div>`);
    }
    return `<div class="setrow ${s.done ? 'done' : ''}"><span class="setno">${j + 1}</span>${cells.join('')}
      ${live ? `<button class="check ${s.done ? 'on' : ''}" data-a="done" data-i="${i}" data-j="${j}" aria-label="Set klaar">✓</button>` : `<button class="icon small" data-a="delset" data-i="${i}" data-j="${j}" aria-label="Set verwijderen">✕</button>`}</div>`;
  }).join('');
  const per = hasWeight(e) && e.implements === 2 ? '<span class="muted small">gewicht per halter</span>' : '';
  const hint = hasWeight(e) && opts ? `<span class="muted small">${opts.length} gewichten mogelijk (${kg(opts[0])}–${kg(opts[opts.length - 1])} kg)</span>` : '';
  return `<div class="sets">${rows}<div class="setfoot"><button data-a="addset" data-i="${i}">+ set</button>${live ? `<button data-a="delset" data-i="${i}" data-j="${it.sets.length - 1}">− set</button>` : ''} ${per} ${hint}</div></div>`;
}

function vPlan() {
  const p = plan();
  if (!p) { S.view = 'home'; return vHome(); }
  const sec = planSeconds(S.lib, p.items);
  const dayMuscles = musclesOfDay(S.lib, p.day);
  const custom = p.focus.join() !== dayMuscles.join();
  return `${header('Voorstel')}
  <main>
    <div class="card">
      <div class="planhead"><div><b>${esc(dayLabel(p.day))}</b> · ${esc(locLabel(p.location))}</div><div class="${sec / 60 > p.minutes + 3 ? 'warn' : ''}">≈ ${mins(sec)} / ${p.minutes} min</div></div>
      <div class="stepper"><button data-a="pmin" data-v="-1">−15</button><span>${p.minutes} min</span><button data-a="pmin" data-v="1">+15</button></div>
      <div class="chips">${p.focus.map(m => `<span class="chip">${esc(m)}</span>`).join('')}${custom ? '<span class="chip alt">aangepast</span>' : ''}</div>
      <div class="row2"><button class="btn" data-a="focus">Spiergroepen</button><button class="btn" data-a="reroll">🎲 Ander voorstel</button></div>
    </div>
    ${p.items.map((it, i) => itemCard(p, it, i, true)).join('')}
    <button class="btn" data-a="add">+ Oefening toevoegen</button>
    <button class="btn primary sticky" data-a="start">Start training</button>
  </main>`;
}

function vWorkout() {
  const p = plan();
  if (!p || p.status !== 'active') { S.view = 'home'; return vHome(); }
  const i = Math.min(p.current || 0, p.items.length - 1);
  const it = p.items[i];
  const e = ex(it?.name);
  const allDone = p.items.every(x => x.sets.every(s => s.done));
  return `${header(`${i + 1} / ${p.items.length}`, 'home', `<button class="icon" data-a="finish" aria-label="Beëindigen">⏹</button>`)}
  <main class="workout">
    <div class="muted small center"><span id="elapsed">${mmss((Date.now() - p.startedAt) / 1000)}</span> · ${esc(dayLabel(p.day))} · ${esc(locLabel(p.location))}</div>
    ${it ? `<div class="card">
      <h2>${esc(it.name)}</h2>
      <div class="muted small">${esc(e?.primary || '')}${e?.secondary.length ? ' · ' + esc(e.secondary.join(', ')) : ''}</div>
      ${e?.instructions ? `<p class="small">${esc(e.instructions)}</p>` : ''}
      ${it.note ? `<div class="note">${esc(it.note)}</div>` : ''}
      ${setEditor(p, it, i, true)}
      <div class="actions"><button data-a="swap" data-i="${i}">⇄ Wissel oefening</button><button data-a="add">+ Oefening</button></div>
    </div>` : '<p>Geen oefeningen.</p>'}
    <div class="row2"><button class="btn" data-a="nav" data-v="-1" ${i === 0 ? 'disabled' : ''}>‹ Vorige</button>
      ${i < p.items.length - 1 ? `<button class="btn primary" data-a="nav" data-v="1">Volgende ›</button>` : `<button class="btn ${allDone ? 'primary' : ''}" data-a="finish">Afronden</button>`}</div>
    <div class="overview">${p.items.map((x, k) => { const d = x.sets.filter(s => s.done).length; return `<button class="ov ${k === i ? 'on' : ''} ${d === x.sets.length ? 'full' : ''}" data-a="jump" data-i="${k}"><span>${esc(x.name)}</span><small>${d}/${x.sets.length}</small></button>`; }).join('')}</div>
  </main>
  ${restBar(p)}`;
}

function restBar(p) {
  if (!p.rest) return '';
  const left = (p.rest.until - Date.now()) / 1000;
  return `<div class="restbar ${left <= 0 ? 'over' : ''}"><div><small>Rust</small><b id="rest">${left > 0 ? mmss(left) : 'Go!'}</b></div>
    <button data-a="rest" data-v="15">+15s</button><button data-a="rest" data-v="0">${left > 0 ? 'Overslaan' : 'Sluiten'}</button></div>`;
}

function vSummary() {
  const p = plan();
  if (!p) { S.view = 'home'; return vHome(); }
  const done = p.items.map(it => ({ it, sets: it.sets.filter(s => s.done) })).filter(x => x.sets.length);
  const vol = done.reduce((a, x) => a + x.sets.reduce((b, s) => b + (s.weight || 0) * (s.reps || 0) * (ex(x.it.name)?.implements || 1), 0), 0);
  const nSets = done.reduce((a, x) => a + x.sets.length, 0);
  return `${header('Training afronden', 'workout')}
  <main>
    <div class="card"><div class="stats"><div><b>${mmss((Date.now() - p.startedAt) / 1000)}</b><small>duur</small></div><div><b>${nSets}</b><small>sets</small></div><div><b>${Math.round(vol).toLocaleString('nl-BE')}</b><small>kg volume</small></div></div></div>
    ${done.map(x => `<div class="li"><b>${esc(x.it.name)}</b><br><span class="muted small">${x.sets.map(s => esc(setLine(ex(x.it.name), s))).join(' · ')}</span></div>`).join('') || '<p class="muted">Nog geen sets afgevinkt.</p>'}
    <label class="lbl">Notitie (optioneel)</label><textarea data-in="note" rows="2">${esc(p.note || '')}</textarea>
    ${nSets ? '<button class="btn primary" data-a="save">Opslaan in log</button>' : ''}
    <button class="btn" data-a="go" data-v="workout">Terug naar training</button>
    <button class="btn danger" data-a="discard">Training weggooien</button>
  </main>`;
}

function vCardio() {
  const list = S.lib.exercises.filter(e => e.type === 'Cardio' && e.active);
  const c = S.cardio || (S.cardio = { name: list.find(e => e.name === 'Walking')?.name || list[0]?.name, minutes: 45, km: '', when: new Date(Date.now() - new Date().getTimezoneOffset() * 6e4).toISOString().slice(0, 16) });
  return `${header('Cardio loggen')}
  <main><div class="card">
    <label class="lbl">Activiteit</label>
    <select data-in="c-name">${list.map(e => `<option ${e.name === c.name ? 'selected' : ''}>${esc(e.name)}</option>`).join('')}</select>
    <label class="lbl">Wanneer</label><input type="datetime-local" data-in="c-when" value="${esc(c.when)}">
    <label class="lbl">Duur (minuten)</label><input inputmode="numeric" data-in="c-min" value="${esc(c.minutes)}">
    <label class="lbl">Afstand (km, optioneel)</label><input inputmode="decimal" data-in="c-km" value="${esc(c.km)}">
    <button class="btn primary" data-a="cardio-save">Opslaan</button>
  </div></main>`;
}

function vHistory() {
  const sess = sessions(S.lib, S.hist);
  return `${header('Historiek')}
  <main><p class="muted small">Laatste ${sess.length} sessies (70 dagen). De volledige historiek staat in je Google Sheet.</p>
  ${sess.map((s, k) => `<div class="card"><div class="item-head" data-a="hx" data-i="${k}"><div><b>${esc(sessionDate(s.t))}</b> · ${esc(dayLabel(s.day))}${s.location ? ' · ' + esc(locLabel(s.location)) : ''}</div><div class="muted small">${s.items.length} oef.</div></div>
    ${S.hx === k ? s.items.map(it => `<div class="small"><b>${esc(it.name)}</b>: ${it.sets.map(x => esc(setLine(ex(it.name) || { type: x.duration ? 'Timed' : 'Weighted' }, x))).join(' · ')}</div>`).join('') : `<div class="muted small">${esc(s.items.map(i => i.name).join(', '))}</div>`}</div>`).join('')}
  </main>`;
}

function vSettings() {
  const c = cfg();
  return `${header('Instellingen')}
  <main><div class="card">
    <label class="lbl">Gebruiker</label><input data-in="s-user" value="${esc(c.user)}">
    <label class="lbl">Apps Script-URL</label><input data-in="s-url" value="${esc(c.apiUrl)}" placeholder="https://script.google.com/macros/s/…/exec" autocapitalize="off" autocorrect="off">
    <label class="lbl">Token</label><input data-in="s-token" value="${esc(c.token)}" autocapitalize="off" autocorrect="off">
    <button class="btn primary" data-a="sync">Opslaan & synchroniseren</button>
    ${S.msg ? `<p class="err">${esc(S.msg)}</p>` : ''}
  </div>
  <div class="card"><p class="small">Bibliotheek: ${S.lib ? S.lib.exercises.length + ' oefeningen, locaties: ' + esc(locs().map(locLabel).join(', ')) : 'niet geladen'}<br>
    Wachtrij: ${store.outbox().length} training(en)</p>
    <button class="btn" data-a="flush">Wachtrij versturen</button>
  </div>
  <p class="muted small center">FitTrick v1.0</p></main>`;
}

/* ---------------- modal ---------------- */

function vModal() {
  const m = S.modal;
  if (!m) return '';
  const p = plan();
  let body = '';
  if (m.type === 'swap' || m.type === 'add') {
    const taken = p.items.map(x => x.name);
    const q = (m.q || '').toLowerCase();
    let list = m.type === 'swap'
      ? alternatives(S.lib, S.hist, p.location, p.items[m.i], taken)
      : eligible(S.lib, p.location).filter(e => !taken.includes(e.name) && e.type !== 'Cardio')
        .sort((a, b) => (S.hist.exercises?.[b.name]?.n || 0) - (S.hist.exercises?.[a.name]?.n || 0));
    if (m.muscle) list = list.filter(e => e.primary === m.muscle);
    if (q) list = list.filter(e => e.name.toLowerCase().includes(q));
    const muscles = Object.keys(S.lib.muscles);
    body = `<h2>${m.type === 'swap' ? 'Wissel ' + esc(p.items[m.i].name) : 'Oefening toevoegen'}</h2>
      <input data-in="m-q" placeholder="Zoeken…" value="${esc(m.q || '')}">
      <select data-in="m-muscle"><option value="">Alle spiergroepen</option>${muscles.map(x => `<option ${x === m.muscle ? 'selected' : ''}>${esc(x)}</option>`).join('')}</select>
      <div class="pick">${list.slice(0, 60).map(e => `<button data-a="pick" data-v="${esc(e.name)}"><b>${esc(e.name)}</b><small>${esc(e.primary)} · ${esc(e.equipment.join(', '))}${S.hist.exercises?.[e.name] ? ' · ' + S.hist.exercises[e.name].n + ' sets gelogd' : ''}</small></button>`).join('') || '<p class="muted">Niets gevonden op deze locatie.</p>'}</div>`;
  } else if (m.type === 'focus') {
    const groups = {};
    for (const [name, mm] of Object.entries(S.lib.muscles)) if (['Push', 'Pull', 'Legs', 'Core'].includes(mm.day)) (groups[mm.day] ||= []).push(name);
    body = `<h2>Spiergroepen</h2><p class="small muted">Kies welke spieren deze training aan bod komen. Buikspieren komen altijd op het einde.</p>
      ${Object.entries(groups).map(([d, ms]) => `<label class="lbl">${esc(d)}</label><div class="chips">${ms.map(x => `<button class="chip ${m.sel.includes(x) ? 'on' : ''}" data-a="fsel" data-v="${esc(x)}">${esc(x)}</button>`).join('')}</div>`).join('')}
      <button class="btn primary" data-a="fapply">Nieuw voorstel</button>`;
  }
  return `<div class="modal" data-a="mclose"><div class="sheet" data-stop>${body}<button class="btn" data-a="mclose">Sluiten</button></div></div>`;
}

/* ---------------- render ---------------- */

function render() {
  if (S.view === 'splash') { $app.innerHTML = vSplash(); return; }
  if (!S.lib && !['settings'].includes(S.view)) S.view = 'home';
  const v = { home: vHome, plan: vPlan, workout: vWorkout, summary: vSummary, cardio: vCardio, history: vHistory, settings: vSettings }[S.view] || vHome;
  const y = window.scrollY;
  $app.innerHTML = v() + vModal();
  if (S.keepScroll) window.scrollTo(0, y);
  S.keepScroll = false;
  keepAwake(S.view === 'workout');
}

/* ---------------- actions ---------------- */

function mutatePlan(fn) {
  const p = plan();
  fn(p);
  store.setPlan(p);
  S.keepScroll = true;
  render();
}

function startRest(p, sec) {
  p.rest = sec > 0 ? { until: Date.now() + sec * 1000, beeped: false } : null;
}

function finishWorkoutRows(p) {
  const rows = [];
  for (const it of p.items) {
    const e = ex(it.name);
    for (const s of it.sets) if (s.done) rows.push({
      exercise: it.name, reps: e?.type === 'Timed' || e?.type === 'Cardio' ? 0 : s.reps, weight: s.weight || 0,
      duration: e?.type === 'Timed' || e?.type === 'Cardio' ? s.duration : 0, distance: s.distance || 0,
      warmup: false, note: '', multiplier: e?.load === 'None' ? (e?.type === 'Cardio' ? 0 : 1) : e?.implements || 1,
    });
  }
  if (rows.length && p.note) rows[0].note = p.note;
  return rows;
}

const actions = {
  enter() { unlockAudio(); const p = plan(); S.view = p?.status === 'active' ? 'workout' : 'home'; render(); if (S.lib && cfg().apiUrl) doSync(true); },
  go(v) { S.view = v; S.modal = null; S.msg = S.view === 'settings' ? S.msg : ''; window.scrollTo(0, 0); render(); },
  loc(v) { setCfg({ location: v }); render(); },
  day(v) { S.day = v; render(); },
  min(v) { const step = S.lib.settings.step; setCfg({ minutes: Math.max(step, Math.min(180, currentMinutes() + Number(v) * step)) }); render(); },
  propose() { const p = plan(); if (p?.status === 'active' && !confirm('Er is nog een training bezig. Toch een nieuw voorstel maken?')) return; store.setPlan(null); newProposal({}); },
  pmin(v) { const p = plan(); const step = S.lib.settings.step; const m = Math.max(step, Math.min(180, p.minutes + Number(v) * step)); setCfg({ minutes: m }); newProposal({ day: p.day, location: p.location, minutes: m, focus: p.customFocus ? p.focus : null, seed: p.seed }); },
  reroll() { const p = plan(); newProposal({ day: p.day, location: p.location, minutes: p.minutes, focus: p.customFocus ? p.focus : null, seed: Math.floor(Math.random() * 1e9) }); },
  focus() { S.modal = { type: 'focus', sel: [...plan().focus] }; render(); },
  fsel(v) { const s = S.modal.sel; const k = s.indexOf(v); k >= 0 ? s.splice(k, 1) : s.push(v); render(); },
  fapply() { const p = plan(); const sel = S.modal.sel; S.modal = null; if (!sel.length) return render(); newProposal({ day: p.day, location: p.location, minutes: p.minutes, focus: sel, seed: p.seed }); },
  expand(_, i) { S.expanded = S.expanded === i ? null : i; S.keepScroll = true; render(); },
  up(_, i) { mutatePlan(p => { [p.items[i - 1], p.items[i]] = [p.items[i], p.items[i - 1]]; }); S.expanded = null; },
  down(_, i) { mutatePlan(p => { [p.items[i + 1], p.items[i]] = [p.items[i], p.items[i + 1]]; }); S.expanded = null; },
  remove(_, i) { mutatePlan(p => { p.items.splice(i, 1); }); S.expanded = null; },
  swap(_, i) { S.modal = { type: 'swap', i }; render(); },
  add() { S.modal = { type: 'add' }; render(); },
  pick(v) {
    const m = S.modal; S.modal = null;
    const e = ex(v);
    const p0 = plan();
    const pr = prescribe(S.lib, S.hist, e, p0.location);
    mutatePlan(p => {
      const item = { name: v, sets: pr.sets, note: pr.note };
      if (m.type === 'swap') {
        const old = p.items[m.i];
        if (old.sets.some(s => s.done)) { old.sets = old.sets.filter(s => s.done); p.items.splice(m.i + 1, 0, item); p.current = m.i + 1; }
        else p.items[m.i] = item;
      } else {
        const at = p.status === 'active' ? (p.current || 0) + 1 : Math.max(0, p.items.findIndex(x => dayOf(S.lib, ex(x.name)) === 'Core'));
        p.items.splice(at < 0 ? p.items.length : at, 0, item);
        if (p.status === 'active') p.current = at;
      }
    });
  },
  mclose() { S.modal = null; render(); },
  w(v, i, j) { mutatePlan(p => { const it = p.items[i]; const opts = optionsFor(p, it.name); const cur = it.sets[j].weight; const nw = cur == null && opts ? opts[0] : stepWeight(opts, cur, Number(v)); it.sets.forEach((s, k) => { if (k >= j && !s.done) s.weight = nw; }); }); },
  r(v, i, j) { mutatePlan(p => { const it = p.items[i]; const nr = Math.max(0, it.sets[j].reps + Number(v)); it.sets.forEach((s, k) => { if (k >= j && !s.done) s.reps = nr; }); }); },
  d(v, i, j) { mutatePlan(p => { const e = ex(p.items[i].name); const step = e.type === 'Cardio' ? 300 : 5; const it = p.items[i]; const nd = Math.max(0, it.sets[j].duration + Number(v) * step); it.sets.forEach((s, k) => { if (k >= j && !s.done) s.duration = nd; }); }); },
  addset(_, i) { mutatePlan(p => { const it = p.items[i]; const last = it.sets[it.sets.length - 1] || { reps: 10, weight: null, duration: 30 }; it.sets.push({ ...last, done: false }); }); },
  delset(_, i, j) { mutatePlan(p => { const it = p.items[i]; if (it.sets.length > 1) it.sets.splice(j, 1); }); },
  start() {
    const p = plan();
    const missing = p.items.filter(it => hasWeight(ex(it.name)) && it.sets.some(s => s.weight == null)).map(it => it.name);
    if (missing.length && !confirm(`Nog geen gewicht gekozen voor:\n${missing.join('\n')}\n\nToch starten? Je kan het tijdens de training invullen.`)) return;
    unlockAudio();
    mutatePlan(p => { p.status = 'active'; p.startedAt = Date.now(); p.current = 0; p.rest = null; });
    S.view = 'workout'; S.expanded = null; render();
  },
  done(_, i, j) {
    unlockAudio();
    mutatePlan(p => {
      const it = p.items[i]; const s = it.sets[j]; const e = ex(it.name);
      if (!s.done && hasWeight(e) && s.weight == null) { alert('Vul eerst het gewicht in.'); return; }
      s.done = !s.done;
      if (s.done) {
        const allDone = it.sets.every(x => x.done);
        const lastOfAll = allDone && i === p.items.length - 1;
        startRest(p, lastOfAll ? 0 : allDone ? Math.min(e?.rest || 60, S.lib.settings.transition) : (e?.rest || 60));
        if (allDone && i < p.items.length - 1) p.current = i + 1;
      }
    });
  },
  rest(v) { mutatePlan(p => { if (!p.rest) return; if (Number(v) > 0) { p.rest.until = Math.max(p.rest.until, Date.now()) + Number(v) * 1000; p.rest.beeped = false; } else p.rest = null; }); },
  nav(v) { mutatePlan(p => { p.current = Math.max(0, Math.min(p.items.length - 1, (p.current || 0) + Number(v))); }); window.scrollTo(0, 0); },
  jump(_, i) { mutatePlan(p => { p.current = i; }); window.scrollTo(0, 0); },
  finish() { S.view = 'summary'; render(); },
  discard() { if (!confirm('Training weggooien? Niets wordt gelogd.')) return; store.setPlan(null); S.view = 'home'; render(); },
  async save() {
    const p = plan();
    const workout = { id: p.id, date: new Date(p.startedAt).toISOString(), day: p.day, location: p.location, rows: finishWorkoutRows(p) };
    store.setPlan(null);
    S.view = 'home'; S.msg = 'Training opgeslagen, bezig met verzenden…'; render();
    const r = await logWorkout(workout);
    S.hist = mergedHistory();
    S.msg = r.pending ? `Opgeslagen op je toestel; verzenden naar Google Sheets lukt nog niet (${r.error || 'offline'}). Ik probeer het later opnieuw.` : 'Training gelogd in Google Sheets ✓';
    render();
  },
  async 'cardio-save'() {
    const c = S.cardio;
    const minutes = Number(String(c.minutes).replace(',', '.'));
    if (!(minutes > 0)) return alert('Vul een duur in.');
    const e = ex(c.name);
    const workout = { id: crypto.randomUUID(), date: new Date(c.when).toISOString(), day: 'Cardio', location: '', rows: [{
      exercise: c.name, reps: 0, weight: 0, duration: Math.round(minutes * 60), distance: Math.round((Number(String(c.km).replace(',', '.')) || 0) * 1000),
      warmup: false, note: '', multiplier: e?.implements || 0 }] };
    S.cardio = null; S.view = 'home'; S.msg = 'Bezig met verzenden…'; render();
    const r = await logWorkout(workout);
    S.hist = mergedHistory();
    S.msg = r.pending ? `Opgeslagen op je toestel; verzenden lukt nog niet (${r.error || 'offline'}).` : `${c.name} gelogd ✓`;
    render();
  },
  hx(_, i) { S.hx = S.hx === i ? null : i; S.keepScroll = true; render(); },
  async sync() { S.msg = ''; await doSync(); if (!S.msg) { S.view = 'home'; render(); } },
  async flush() { const r = await flushOutbox(); S.msg = r.pending ? `Nog ${r.pending} in wachtrij: ${r.error || 'niet gekoppeld'}` : `${r.sent} verstuurd ✓`; render(); },
};

$app.addEventListener('click', ev => {
  const el = ev.target.closest('[data-a], [data-stop]');
  if (!el || el.hasAttribute('data-stop') && !ev.target.closest('[data-a]')) return;
  const t = ev.target.closest('[data-a]');
  if (t.classList.contains('modal') && ev.target !== t) return; // clicks inside the sheet
  const fn = actions[t.dataset.a];
  if (!fn || t.disabled) return;
  const i = t.dataset.i != null ? Number(t.dataset.i) : undefined;
  const j = t.dataset.j != null ? Number(t.dataset.j) : undefined;
  fn(t.dataset.v, i, j);
});

$app.addEventListener('change', ev => {
  const el = ev.target.closest('[data-in]');
  if (!el) return;
  const k = el.dataset.in, v = el.value;
  const i = Number(el.dataset.i), j = Number(el.dataset.j);
  const n = Number(String(v).replace(',', '.'));
  if (k === 'weight') return mutatePlan(p => { const it = p.items[i]; const w = v.trim() === '' ? null : n; if (w == null || isFinite(w)) it.sets.forEach((s, x) => { if (x >= j && !s.done) s.weight = w; }); });
  if (k === 'reps') return mutatePlan(p => { if (isFinite(n)) p.items[i].sets.forEach((s, x) => { if (x >= j && !s.done) s.reps = Math.max(0, Math.round(n)); }); });
  if (k === 'duration') return mutatePlan(p => { const e = ex(p.items[i].name); if (isFinite(n)) p.items[i].sets.forEach((s, x) => { if (x >= j && !s.done) s.duration = Math.round(e.type === 'Cardio' ? n * 60 : n); }); });
  if (k === 'distance') return mutatePlan(p => { p.items[i].sets[j].distance = isFinite(n) ? Math.round(n * 1000) : 0; });
  if (k === 'note') return mutatePlan(p => { p.note = v; });
  if (k.startsWith('c-')) { S.cardio[{ 'c-name': 'name', 'c-when': 'when', 'c-min': 'minutes', 'c-km': 'km' }[k]] = v; return; }
  if (k.startsWith('s-')) { setCfg({ [{ 's-user': 'user', 's-url': 'apiUrl', 's-token': 'token' }[k]]: v.trim() }); return; }
  if (k === 'm-muscle') { S.modal.muscle = v; render(); }
});
$app.addEventListener('input', ev => {
  const el = ev.target.closest('[data-in="m-q"]');
  if (!el) return;
  S.modal.q = el.value;
  const pos = el.selectionStart;
  render();
  const again = $app.querySelector('[data-in="m-q"]');
  again.focus(); again.setSelectionRange(pos, pos);
});

/* ---------------- timers ---------------- */

setInterval(() => {
  if (S.view !== 'workout') return;
  const p = plan();
  if (!p) return;
  const el = document.getElementById('elapsed');
  if (el) el.textContent = mmss((Date.now() - p.startedAt) / 1000);
  if (p.rest) {
    const left = (p.rest.until - Date.now()) / 1000;
    const r = document.getElementById('rest');
    if (r) r.textContent = left > 0 ? mmss(left) : 'Go!';
    if (left <= 0 && !p.rest.beeped) { p.rest.beeped = true; store.setPlan(p); beep(); S.keepScroll = true; render(); }
  }
}, 500);

/* ---------------- start ---------------- */

loadLib();
render();
if (!S.lib && new URLSearchParams(location.search).has('dev')) doSync(true); // local test data
if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('sw.js');
window.addEventListener('online', () => flushOutbox().then(() => { S.hist = mergedHistory(); }));
