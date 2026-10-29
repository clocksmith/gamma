"use strict";
// Hack2Hire 68b8f94083188776facc8fc9 (Minimum Menu Order Cost II) over an INFERRED spec; qualification unknown.

function compareIds(x, y) {
  const n = Math.min(x.length, y.length);
  for (let i = 0; i < n; i++) if (x[i] !== y[i]) return x[i] < y[i] ? -1 : 1;
  return x.length - y.length;
}

function solve(menu, userWants) {
  const index = new Map();
  userWants.forEach((x, i) => index.set(x, i));
  const w = userWants.length, full = (1 << w) - 1;
  const containing = Array.from({ length: w }, () => []);
  for (const [entryId, price, items] of menu) {
    const parts = items.split(",");
    if (!parts.every((x) => index.has(x))) continue;
    let mask = 0;
    for (const x of parts) mask |= 1 << index.get(x);
    for (let bit = 0; bit < w; bit++) if ((mask >> bit) & 1) containing[bit].push([mask, price, entryId]);
  }
  const lowBit = (rem) => 31 - Math.clz32(rem & -rem);
  const best = new Array(full + 1).fill(null);
  best[0] = 0;
  for (let rem = 1; rem <= full; rem++) {
    for (const [mask, price] of containing[lowBit(rem)]) {
      if ((mask & ~rem) === 0 && best[rem ^ mask] !== null) {
        const c = price + best[rem ^ mask];
        if (best[rem] === null || c < best[rem]) best[rem] = c;
      }
    }
  }
  if (best[full] === null) return [];
  const found = [], chosen = [];
  const walk = (rem) => {
    if (rem === 0) { found.push(chosen.slice().sort()); return; }
    for (const [mask, price, entryId] of containing[lowBit(rem)]) {
      if ((mask & ~rem) === 0 && best[rem ^ mask] !== null && price + best[rem ^ mask] === best[rem]) {
        chosen.push(entryId);
        walk(rem ^ mask);
        chosen.pop();
      }
    }
  };
  walk(full);
  found.sort(compareIds);
  return found;
}

function cheapestExactOrders(menu, userWants) { return solve(menu, userWants); }

module.exports = solve;
module.exports.cheapestExactOrders = cheapestExactOrders;
