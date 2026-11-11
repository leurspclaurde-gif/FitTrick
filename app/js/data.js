// Local persistence, offline outbox and the Apps Script API.

const K = { cfg: 'ft.cfg', lib: 'ft.lib', hist: 'ft.hist', plan: 'ft.plan', outbox: 'ft.outbox', local: 'ft.local', synced: 'ft.synced' };

export function load(key, fallback) {
  try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
}
export function save(key, value) {
  try { value == null ? localStorage.removeItem(key) : localStorage.setItem(key, JSON.stringify(value)); } catch (e) { console.warn('save failed', key, e); }
}

export const store = {
  cfg: () => ({ user: 'Patrick', apiUrl: '', token: '', location: '', minutes: 0, ...load(K.cfg, {}) }),
  setCfg: c => save(K.cfg, c),
  rawLib: () => load(K.lib, null),
  hist: () => load(K.hist, { exercises: {}, recent: [] }),
  plan: () => load(K.plan, null),
  setPlan: p => save(K.plan, p),
  outbox: () => load(K.outbox, []),
  local: () => load(K.local, []),
  syncedAt: () => load(K.synced, null),
};

const isDev = () => new URLSearchParams(location.search).has('dev');

async function call(cfg, body) {
  const res = await fetch(cfg.apiUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain;charset=utf-8' }, // avoids a CORS preflight on Apps Script
    body: JSON.stringify({ ...body, token: cfg.token, user: cfg.user }),
    redirect: 'follow',
  });
  if (!res.ok) throw new Error('HTTP ' + res.status);
  const data = await res.json();
  if (!data.ok) throw new Error(data.error || 'Onbekende fout');
  return data;
}

/** Fetches library + history. Returns true when fresh data was stored. */
export async function sync() {
  const cfg = store.cfg();
  let data;
  if (isDev() && !cfg.apiUrl) {
    const [library, history] = await Promise.all(['library', 'history'].map(n => fetch(`../dev-data/${n}.json`).then(r => r.json())));
    data = { library, history: load('ft.devhist', null) || history };
  } else {
    if (!cfg.apiUrl || !cfg.token) throw new Error('Nog niet gekoppeld: vul de Apps Script-URL en token in bij Instellingen.');
    await flushOutbox();
    data = await call(cfg, { action: 'bootstrap' });
  }
  save(K.lib, data.library);
  save(K.hist, data.history);
  // workouts still in the outbox are not on the server yet: keep them locally
  const pending = new Set(store.outbox().map(w => w.id));
  save(K.local, store.local().filter(w => pending.has(w.id)));
  save(K.synced, Date.now());
  return true;
}

/** Merges local (not yet synced) workouts into the server history. */
export function mergedHistory() {
  const h = store.hist();
  const exercises = { ...h.exercises };
  const recent = [...(h.recent || [])];
  const known = new Set(recent.map(r => r[8]));
  for (const w of store.local()) {
    if (known.has(w.id)) continue;
    const t = new Date(w.date).getTime();
    const by = new Map();
    for (const r of w.rows) {
      const set = [r.reps, r.weight, r.duration, r.distance, r.warmup ? 1 : 0];
      recent.push([t, r.exercise, ...set, r.multiplier, w.id, w.location, w.day]);
      if (!by.has(r.exercise)) by.set(r.exercise, []);
      by.get(r.exercise).push(set);
    }
    for (const [name, sets] of by) {
      const prev = exercises[name];
      if (!prev || prev.last <= t) exercises[name] = { n: (prev?.n || 0) + sets.length, last: t, sets };
    }
  }
  return { exercises, recent };
}

/** Stores a finished workout locally and tries to send it to the log sheet. */
export async function logWorkout(workout) {
  save(K.local, [...store.local(), workout]);
  save(K.outbox, [...store.outbox(), workout]);
  return flushOutbox();
}

export async function flushOutbox() {
  const cfg = store.cfg();
  let box = store.outbox();
  if (!box.length) return { sent: 0, pending: 0 };
  if (isDev() && !cfg.apiUrl) {
    // dev: append to a local copy of the history instead of a sheet
    const h = load('ft.devhist', null) || store.hist();
    for (const w of box) {
      const t = new Date(w.date).getTime();
      for (const r of w.rows) h.recent.push([t, r.exercise, r.reps, r.weight, r.duration, r.distance, r.warmup ? 1 : 0, r.multiplier, w.id, w.location, w.day]);
    }
    save('ft.devhist', h);
    save(K.outbox, []);
    return { sent: box.length, pending: 0 };
  }
  if (!cfg.apiUrl || !cfg.token) return { sent: 0, pending: box.length };
  let sent = 0;
  for (const w of [...box]) {
    try {
      await call(cfg, { action: 'log', workout: w });
      sent++;
      box = box.filter(x => x.id !== w.id);
      save(K.outbox, box);
    } catch (e) {
      return { sent, pending: box.length, error: e.message };
    }
  }
  return { sent, pending: 0 };
}
