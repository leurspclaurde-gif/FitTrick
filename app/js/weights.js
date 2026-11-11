// Available loads per location/equipment, computed from the Equipment and Plates tabs.

export function parseList(v) {
  return String(v ?? '')
    .split(/[;,\s]+/)
    .map(s => Number(s.replace(',', '.')))
    .filter(n => isFinite(n) && n > 0);
}

const round2 = n => Math.round(n * 100) / 100;

/**
 * Returns a sorted array of loads (kg per implement) possible for `load` at `location`,
 * or null when any value is allowed (no equipment row / bodyweight).
 */
export function loadOptions(lib, location, load, impl = 1) {
  if (!load || load === 'None') return null;
  const row = lib.equipment.find(e => e.location === location && e.name === load && e.available);
  if (!row) return null;
  switch (row.loading) {
    case 'Fixed': {
      const list = [...new Set(parseList(row.fixed).map(round2))].sort((a, b) => a - b);
      return list.length ? list : null;
    }
    case 'Stack': {
      const min = Number(row.stackMin) || 0, max = Number(row.stackMax) || 0, step = Number(row.stackStep) || 0;
      if (!(step > 0) || max < min) return null;
      const out = [];
      for (let w = min; w <= max + 1e-9; w += step) out.push(round2(w));
      return out;
    }
    case 'Plates': {
      const bar = Number(row.bar) || 0;
      const n = Math.max(1, Number(impl) || 1);
      // per side of one implement: floor(qty / (2 sides * implements))
      let sums = new Set([0]);
      // plates listed for this equipment, or for "*" (shared by all plate-loaded equipment at the location)
      for (const p of lib.plates.filter(p => p.location === location && (p.equipment === load || p.equipment === '*'))) {
        const per = Math.floor((Number(p.qty) || 0) / (2 * n));
        const next = new Set();
        for (const s of sums) for (let k = 0; k <= per; k++) next.add(round2(s + k * p.kg));
        sums = next;
      }
      return [...sums].map(s => round2(bar + 2 * s)).sort((a, b) => a - b);
    }
    default:
      return null;
  }
}

export function nearest(list, w) {
  if (!list || !list.length || w == null) return w;
  let best = list[0];
  for (const x of list) if (Math.abs(x - w) < Math.abs(best - w) - 1e-9) best = x;
  return best;
}

export function stepWeight(list, w, dir, freeStep = 2.5) {
  if (!list || !list.length) return Math.max(0, round2((Number(w) || 0) + dir * freeStep));
  if (w == null) return list[0];
  if (dir > 0) return list.find(x => x > w + 1e-9) ?? list[list.length - 1];
  for (let i = list.length - 1; i >= 0; i--) if (list[i] < w - 1e-9) return list[i];
  return list[0];
}
