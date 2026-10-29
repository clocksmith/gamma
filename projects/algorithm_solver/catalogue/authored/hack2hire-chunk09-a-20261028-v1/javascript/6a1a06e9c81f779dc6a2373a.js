"use strict";
// Hack2Hire 6a1a06e9c81f779dc6a2373a (AI Token Billing Calculation, variant 2 of 3) over an INFERRED spec; qualification unknown.

function solve(sessions, pricing) {
  const prices = new Map();
  for (const row of pricing) {
    const f = row.split(",");
    prices.set(f[0], [Number(f[1]), Number(f[2]), Number(f[3]), Number(f[4])]);
  }
  const left = new Map();
  const totals = new Map();
  for (const row of sessions) {
    const f = row.split(",");
    const p = prices.get(f[3]);
    const key = f[0] + "," + f[3];
    let charge = 0;
    if (!left.has(key)) { left.set(key, p[3]); charge = p[2]; }
    let remaining = left.get(key);
    const tin = Number(f[1]), tout = Number(f[2]);
    let use = tin < remaining ? tin : remaining;
    remaining -= use; charge += (tin - use) * p[0];
    use = tout < remaining ? tout : remaining;
    remaining -= use; charge += (tout - use) * p[1];
    left.set(key, remaining);
    totals.set(f[0], (totals.get(f[0]) || 0) + charge);
  }
  const users = [...totals.keys()].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  return users.map((u) => [u, totals.get(u)]);
}

function calculateMonthlySpend(sessions, pricing) { return solve(sessions, pricing); }

module.exports = solve;
module.exports.calculateMonthlySpend = calculateMonthlySpend;
