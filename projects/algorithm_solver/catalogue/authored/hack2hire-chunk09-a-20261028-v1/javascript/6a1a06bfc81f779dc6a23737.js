"use strict";
// Hack2Hire 6a1a06bfc81f779dc6a23737 (AI Token Billing Calculation, variant 1 of 3) over an INFERRED spec; qualification unknown.

function solve(sessions, pricing) {
  const prices = new Map();
  for (const row of pricing) {
    const f = row.split(",");
    prices.set(f[0], [Number(f[1]), Number(f[2])]);
  }
  const totals = new Map();
  for (const row of sessions) {
    const f = row.split(",");
    const p = prices.get(f[3]);
    totals.set(f[0], (totals.get(f[0]) || 0) + Number(f[1]) * p[0] + Number(f[2]) * p[1]);
  }
  const users = [...totals.keys()].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  return users.map((u) => [u, totals.get(u)]);
}

function calculateMonthlySpend(sessions, pricing) { return solve(sessions, pricing); }

module.exports = solve;
module.exports.calculateMonthlySpend = calculateMonthlySpend;
