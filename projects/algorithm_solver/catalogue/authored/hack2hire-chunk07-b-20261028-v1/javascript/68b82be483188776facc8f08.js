"use strict";
// Hack2Hire 68b82be483188776facc8f08 (Minimum Menu Order Cost I, level 1) over an INFERRED spec; qualification unknown.

const LEVEL = 1;

function solve(menu, userWants) {
  const index = new Map();
  userWants.forEach((x, i) => index.set(x, i));
  const full = (1 << userWants.length) - 1;
  const cheapest = new Map();
  for (const [, price, items] of menu) {
    let mask = 0;
    for (const x of items.split(",")) if (index.has(x)) mask |= 1 << index.get(x);
    if (mask && (!cheapest.has(mask) || price < cheapest.get(mask))) cheapest.set(mask, price);
  }
  const masks = Array.from(cheapest.keys()), prices = masks.map((e) => cheapest.get(e));
  const cost = new Float64Array(full + 1).fill(-1), count = new Int32Array(full + 1);
  cost[0] = 0;
  for (let mask = 0; mask <= full; mask++) {
    const c = cost[mask];
    if (c < 0) continue;
    for (let t = 0; t < masks.length; t++) {
      const nm = mask | masks[t];
      if (nm === mask) continue;
      const nc = c + prices[t], nk = count[mask] + 1;
      if (cost[nm] < 0 || nc < cost[nm] || (nc === cost[nm] && nk < count[nm])) { cost[nm] = nc; count[nm] = nk; }
    }
  }
  if (LEVEL === 1) return cost[full] < 0 ? -1 : cost[full];
  return cost[full] < 0 ? [-1, -1] : [cost[full], count[full]];
}

function minOrderCost(menu, userWants) { return solve(menu, userWants); }

module.exports = solve;
module.exports.minOrderCost = minOrderCost;
