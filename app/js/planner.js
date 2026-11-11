// Library normalisation, history analysis and the workout proposal engine. Pure functions (no DOM).
import { loadOptions, nearest, stepWeight } from './weights.js';

const bool = v => v === true || /^(true|yes|ja|y|1|x)$/i.test(String(v ?? '').trim());
const num = (v, d = 0) => { const n = Number(String(v ?? '').replace(',', '.')); return isFinite(n) && String(v ?? '').trim() !== '' ? n : d; };
const list = v => String(v ?? '').split(/\s*[;,]\s*/).map(s => s.trim()).filter(Boolean);

export const DAY_TYPES = ['Push', 'Pull', 'Legs', 'Full Body'];
const STRENGTH_DAYS = ['Push', 'Pull', 'Legs'];

/* ---------------- library ---------------- */

export function normalizeLibrary(raw) {
  const settings = {};
  for (const r of raw.settings || []) settings[String(r.Key).trim()] = r.Value;
  const muscles = {};
  for (const r of raw.muscles || []) {
    const name = String(r.Muscle || '').trim();
    if (name) muscles[name] = { day: String(r.Day || '').trim(), weekly: num(r['Weekly sets'], 6), priority: num(r.Priority, 1) };
  }
  const exercises = (raw.exercises || []).map(r => ({
    name: String(r.Exercise).trim(),
    active: r.Active === undefined || r.Active === '' ? true : bool(r.Active),
    primary: String(r.Primary || '').trim(),
    secondary: list(r.Secondary),
    equipment: list(r.Equipment),
    load: String(r.Load || 'None').trim() || 'None',
    implements: num(r.Implements, 1),
    type: String(r.Type || 'Weighted').trim(),
    mechanics: String(r.Mechanics || 'Isolation').trim(),
    repMin: num(r.RepMin, 8), repMax: num(r.RepMax, 12),
    sets: Math.max(1, num(r.Sets, 3)),
    rest: num(r.RestSec, 60), secPerRep: num(r.SecPerRep, 3),
    instructions: String(r.Instructions || '').trim(),
  })).filter(e => e.name);
  const equipment = (raw.equipment || []).map(r => ({
    location: String(r.Location || '').trim(),
    name: String(r.Equipment || '').trim(),
    available: bool(r.Available),
    loading: String(r.Loading || 'None').trim(),
    bar: num(r['Bar kg']),
    fixed: r['Fixed weights'],
    stackMin: num(r['Stack min']), stackMax: num(r['Stack max']), stackStep: num(r['Stack step']),
  })).filter(e => e.location && e.name);
  const plates = (raw.plates || []).map(r => ({
    location: String(r.Location || '').trim(), equipment: String(r.Equipment || '').trim(),
    kg: num(r['Plate kg']), qty: num(r.Quantity),
  })).filter(p => p.kg > 0);
  const lib = {
    exercises, equipment, plates, muscles,
    settings: {
      user: String(settings.User || 'Patrick'),
      order: list(settings['PPL Order'] || 'Push, Pull, Legs'),
      minutes: num(settings['Default minutes'], 60),
      step: num(settings['Duration step'], 15),
      transition: num(settings['Transition sec'], 90),
      minCore: num(settings['Min core exercises'], 1),
      window: num(settings['Weekly window days'], 7),
      variety: num(settings['Variety sessions'], 2),
    },
  };
  lib.byName = new Map(exercises.map(e => [e.name, e]));
  lib.locations = [...new Set(equipment.map(e => e.location))];
  return lib;
}

export function dayOf(lib, ex) {
  return lib.muscles[ex.primary]?.day || 'Other';
}

export function availableEquipment(lib, location) {
  const s = new Set(['Bodyweight']);
  for (const e of lib.equipment) if (e.location === location && e.available) s.add(e.name);
  return s;
}

export function eligible(lib, location) {
  const eq = availableEquipment(lib, location);
  return lib.exercises.filter(e => e.active && e.equipment.every(x => eq.has(x)));
}

/* ---------------- history ---------------- */

/** Groups compact recent rows [t, name, reps, w, dur, dist, warm, mult, key, loc, day] into sessions (newest first). */
export function sessions(lib, hist) {
  const map = new Map();
  for (const r of hist.recent || []) {
    const [t, name, reps, w, dur, dist, warm, mult, key, loc, day] = r;
    let s = map.get(key);
    if (!s) map.set(key, s = { key, t, location: loc, day, items: new Map() });
    s.t = Math.min(s.t, t);
    let it = s.items.get(name);
    if (!it) s.items.set(name, it = { name, sets: [] });
    it.sets.push({ reps, weight: w, duration: dur, distance: dist, warmup: !!warm, mult });
  }
  const out = [...map.values()].map(s => {
    const items = [...s.items.values()];
    if (!s.day) s.day = inferDay(lib, items.map(i => i.name));
    return { ...s, items };
  });
  return out.sort((a, b) => b.t - a.t);
}

export function inferDay(lib, names) {
  const count = {};
  for (const n of names) {
    const ex = lib.byName.get(n);
    const d = ex ? dayOf(lib, ex) : null;
    if (d && STRENGTH_DAYS.includes(d)) count[d] = (count[d] || 0) + 1;
  }
  const best = Object.entries(count).sort((a, b) => b[1] - a[1])[0];
  if (!best) return names.some(n => lib.byName.get(n)?.type === 'Cardio') ? 'Cardio' : 'Other';
  return best[0];
}

export function nextDay(lib, sess) {
  const order = lib.settings.order.length ? lib.settings.order : STRENGTH_DAYS;
  const last = sess.find(s => order.includes(s.day));
  if (!last) return order[0];
  return order[(order.indexOf(last.day) + 1) % order.length];
}

/** Working sets per muscle in the last `days` days (primary = 1, secondary = 0.5). */
export function muscleVolume(lib, sess, now, days) {
  const vol = {};
  const from = now - days * 864e5;
  for (const s of sess) {
    if (s.t < from) continue;
    for (const it of s.items) {
      const ex = lib.byName.get(it.name);
      if (!ex) continue;
      const n = it.sets.filter(x => !x.warmup).length;
      vol[ex.primary] = (vol[ex.primary] || 0) + n;
      for (const m of ex.secondary) vol[m] = (vol[m] || 0) + n * 0.5;
    }
  }
  return vol;
}

/* ---------------- prescription ---------------- */

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

/** Proposes sets for an exercise from its last performance and the loads available at the location. */
export function prescribe(lib, hist, ex, location) {
  const options = loadOptions(lib, location, ex.load, ex.implements);
  const last = hist.exercises?.[ex.name];
  const work = (last?.sets || []).filter(s => !s[4]);
  const n = ex.sets;
  const mk = (reps, weight, duration = 0) => Array.from({ length: n }, () => ({ reps, weight, duration, done: false }));

  if (ex.type === 'Cardio') {
    const lastMin = work.length ? Math.round(Math.max(...work.map(s => s[2])) / 60) : 0;
    const min = clamp(lastMin || ex.repMin, ex.repMin, ex.repMax);
    return { sets: [{ reps: 0, weight: 0, duration: min * 60, distance: 0, done: false }], options, note: last ? 'Vorige keer ' + lastMin + ' min' : '' };
  }
  if (ex.type === 'Timed') {
    const lastDur = work.length ? Math.max(...work.map(s => s[2])) : 0;
    const dur = lastDur ? clamp(lastDur + 5, ex.repMin, ex.repMax) : ex.repMin;
    // loaded holds/carries (farmer's carry, weighted wall sit) keep their weight
    const lastW = work.length ? Math.max(...work.map(s => s[1])) : 0;
    const w = ex.load === 'None' ? 0 : lastW ? (options ? nearest(options, lastW) : lastW) : null;
    return { sets: mk(0, w, dur), options, note: lastDur ? `Vorige keer ${lastDur}s${lastW ? ' @ ' + fmtKg(lastW) : ''}` : 'Nieuw' };
  }
  if (!work.length) {
    const w = ex.type === 'Weighted' ? (options ? null : null) : 0;
    return { sets: mk(ex.repMin, w), options, note: 'Nieuw — kies je gewicht' };
  }
  const maxW = Math.max(...work.map(s => s[1]));
  const repsAt = Math.min(...work.filter(s => s[1] === maxW).map(s => s[0]));
  const lastTxt = `Vorige keer ${work.length}× ${repsAt}${maxW ? ' @ ' + fmtKg(maxW) : ''}`;
  if (ex.type !== 'Weighted' || !maxW) {
    const maxReps = Math.max(...work.map(s => s[0]));
    return { sets: mk(clamp(maxReps + 1, ex.repMin, Math.max(ex.repMax, maxReps + 1)), 0), options, note: lastTxt };
  }
  let w = options ? nearest(options, maxW) : maxW;
  let reps;
  if (repsAt >= ex.repMax) {
    // next available load above the last one (rounding to the location's loads may already be a step up)
    const up = options ? stepWeight(options, maxW, +1) : maxW + 2.5;
    if (up > maxW) { w = up; reps = ex.repMin; } else reps = ex.repMax;
  } else {
    reps = clamp(repsAt + 1, ex.repMin, ex.repMax);
  }
  return { sets: mk(reps, w), options, note: lastTxt, progressed: w > maxW };
}

export function fmtKg(w) {
  return (Math.round(w * 100) / 100).toString().replace('.', ',') + ' kg';
}

/* ---------------- time ---------------- */

export function itemSeconds(lib, item) {
  const ex = lib.byName.get(item.name);
  if (!ex) return 0;
  if (ex.type === 'Cardio') return item.sets.reduce((a, s) => a + (s.duration || 0), 0);
  let work = 0;
  for (const s of item.sets) work += ex.type === 'Timed' ? (s.duration || ex.repMin) : (s.reps || ex.repMin) * ex.secPerRep;
  return Math.round(work + Math.max(0, item.sets.length - 1) * ex.rest + lib.settings.transition);
}

export const planSeconds = (lib, items) => items.reduce((a, it) => a + itemSeconds(lib, it), 0);

/* ---------------- proposal ---------------- */

function rng(seed) {
  let x = (seed >>> 0) || 1;
  return () => { x ^= x << 13; x ^= x >>> 17; x ^= x << 5; return ((x >>> 0) % 10000) / 10000; };
}

export function musclesOfDay(lib, day) {
  const days = day === 'Full Body' ? STRENGTH_DAYS : [day];
  return Object.entries(lib.muscles).filter(([, m]) => days.includes(m.day)).map(([k]) => k);
}

/**
 * Builds a workout proposal.
 * opts: {day, location, minutes, focus?: string[] (muscles), seed?, now?, exclude?: string[]}
 */
export function propose(lib, hist, opts) {
  const now = opts.now ?? Date.now();
  const random = rng(opts.seed ?? now);
  const sess = sessions(lib, hist);
  const vol = muscleVolume(lib, sess, now, lib.settings.window);
  const focus = opts.focus?.length ? opts.focus : musclesOfDay(lib, opts.day);
  const exclude = new Set(opts.exclude || []);
  const pool = eligible(lib, opts.location).filter(e => !exclude.has(e.name) && e.type !== 'Cardio' && e.primary !== 'Mobility');

  // recently used exercises (variety): same-day sessions first
  const recentUse = new Map();
  sess.filter(s => s.day === opts.day).slice(0, lib.settings.variety)
    .forEach((s, i) => s.items.forEach(it => { if (!recentUse.has(it.name)) recentUse.set(it.name, i); }));

  const need = {};
  for (const m of focus) {
    const mm = lib.muscles[m] || { weekly: 6, priority: 1 };
    need[m] = (Math.max(0, mm.weekly - (vol[m] || 0)) + mm.weekly * 0.3) * mm.priority;
  }
  // core exercises rotate across all recent sessions, not only same-day ones
  const recentAny = new Map();
  sess.slice(0, 4).forEach((s, i) => s.items.forEach(it => { if (!recentAny.has(it.name)) recentAny.set(it.name, i); }));
  const fam = ex => 0.55 + 0.45 * Math.min(1, Math.log1p(hist.exercises?.[ex.name]?.n || 0) / Math.log1p(60));
  const variety = ex => recentUse.has(ex.name) ? (recentUse.get(ex.name) === 0 ? 0.35 : 0.7) : 1;

  const score = (ex, slot) => {
    const base = (need[ex.primary] || 0) + ex.secondary.reduce((a, m) => a + (need[m] || 0) * 0.3, 0);
    if (!(need[ex.primary] > 0)) return 0;
    const comp = ex.mechanics === 'Compound' ? (slot < 2 ? 1.5 : 1.05) : (slot < 1 ? 0.7 : 1);
    return base * fam(ex) * variety(ex) * comp * (0.8 + 0.4 * random());
  };
  const makeItem = ex => {
    const p = prescribe(lib, hist, ex, opts.location);
    return { name: ex.name, sets: p.sets, note: p.note };
  };

  const budget = Math.max(15, opts.minutes) * 60;
  const items = [];

  // core finisher(s) are reserved first so they always fit
  const corePool = pool.filter(e => dayOf(lib, e) === 'Core' && !focus.includes(e.primary));
  const coreItems = [];
  const coreNeed = m => { const mm = lib.muscles[m] || { weekly: 6, priority: 1 }; return (Math.max(0, mm.weekly - (vol[m] || 0)) + mm.weekly * 0.3) * mm.priority; };
  const coreVariety = ex => recentAny.has(ex.name) ? [0.25, 0.45, 0.65, 0.8][recentAny.get(ex.name)] : 1;
  const coreScore = ex => (coreNeed(ex.primary) + 1) * fam(ex) * coreVariety(ex) * (0.7 + 0.6 * random());
  const pickCore = () => {
    const c = corePool.filter(e => !coreItems.some(i => i.name === e.name))
      .map(e => [e, coreScore(e) * (coreItems.some(i => lib.byName.get(i.name).primary === e.primary) ? 0.4 : 1)])
      .sort((a, b) => b[1] - a[1])[0];
    return c ? makeItem(c[0]) : null;
  };
  for (let i = 0; i < Math.max(1, lib.settings.minCore); i++) { const c = pickCore(); if (c) coreItems.push(c); }
  let remaining = budget - planSeconds(lib, coreItems);

  const mainPool = pool.filter(e => focus.includes(e.primary));
  // at most `cap` exercises per primary muscle; relaxed when nothing else fits the time
  let cap = 2;
  while (true) {
    const used = new Set(items.map(i => i.name));
    const perMuscle = {};
    for (const i of items) { const p = lib.byName.get(i.name).primary; perMuscle[p] = (perMuscle[p] || 0) + 1; }
    const cands = mainPool.filter(e => !used.has(e.name) && (perMuscle[e.primary] || 0) < cap)
      .map(e => [e, score(e, items.length)]).filter(c => c[1] > 0).sort((a, b) => b[1] - a[1]);
    let picked = null;
    for (const [ex] of cands.slice(0, 12)) {
      const it = makeItem(ex);
      const sec = itemSeconds(lib, it);
      if (sec <= remaining + 60 || items.length === 0) { picked = [ex, it, sec]; break; }
    }
    if (!picked) { if (cap < 3 && remaining > 5 * 60) { cap++; continue; } break; }
    const [ex, it, sec] = picked;
    items.push(it);
    remaining -= sec;
    // diminishing returns: the next exercise for the same muscle scores lower, but never zero,
    // so the time budget decides when the workout is full
    need[ex.primary] = (need[ex.primary] || 0) * 0.45;
    for (const m of ex.secondary) if (need[m] != null) need[m] *= 0.8;
    if (items.length > 14) break;
  }
  // spare time: an extra core exercise
  while (remaining > 0 && coreItems.length < 3) {
    const c = pickCore();
    if (!c || itemSeconds(lib, c) > remaining + 30) break;
    coreItems.push(c);
    remaining -= itemSeconds(lib, c);
  }

  // compounds first, then by the muscle order of the Muscles tab (chest before shoulders before triceps, ...)
  const mOrder = Object.keys(lib.muscles);
  const order = it => { const ex = lib.byName.get(it.name); return (ex.mechanics === 'Compound' ? 0 : 100) + Math.max(0, mOrder.indexOf(ex.primary)) + (ex.type === 'Weighted' ? 0 : 0.5); };
  items.sort((a, b) => order(a) - order(b));
  const all = [...items, ...coreItems];
  return { day: opts.day, location: opts.location, minutes: opts.minutes, focus, items: all, seconds: planSeconds(lib, all) };
}

/** Alternatives for swapping an exercise: same primary muscle first, then same day. */
export function alternatives(lib, hist, location, item, takenNames) {
  const cur = lib.byName.get(item.name);
  const taken = new Set(takenNames);
  return eligible(lib, location)
    .filter(e => e.name !== item.name && !taken.has(e.name) && e.type !== 'Cardio')
    .map(e => {
      let s = 0;
      if (cur) {
        if (e.primary === cur.primary) s += 10;
        else if (dayOf(lib, e) === dayOf(lib, cur)) s += 3; else s -= 20;
        s += e.secondary.filter(m => cur.secondary.includes(m)).length;
        if (e.mechanics === cur.mechanics) s += 1;
      }
      s += Math.min(3, Math.log1p(hist.exercises?.[e.name]?.n || 0));
      return [e, s];
    })
    .filter(x => x[1] > -10)
    .sort((a, b) => b[1] - a[1])
    .map(x => x[0]);
}
