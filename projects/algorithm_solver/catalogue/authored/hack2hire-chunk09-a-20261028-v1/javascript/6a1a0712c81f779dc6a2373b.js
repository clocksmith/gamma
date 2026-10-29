"use strict";
// Hack2Hire 6a1a0712c81f779dc6a2373b (AI Token Billing Calculation, variant 3 of 3) over an INFERRED spec; qualification unknown.

function solve(sessions, pricing) {
  const prices = new Map();
  for (const row of pricing) {
    const f = row.split(",");
    prices.set(f[0], [Number(f[1]), Number(f[2]), Number(f[3]), Number(f[4]), Number(f[5])]);
  }
  const pairs = new Map(); // "user,plan" -> [user, plan, remaining free tokens, uncapped usage]
  for (const row of sessions) {
    const f = row.split(",");
    const p = prices.get(f[3]);
    const key = f[0] + "," + f[3];
    let s = pairs.get(key);
    if (s === undefined) { s = [f[0], f[3], p[3], 0]; pairs.set(key, s); }
    const tin = Number(f[1]), tout = Number(f[2]);
    let use = tin < s[2] ? tin : s[2];
    s[2] -= use; s[3] += (tin - use) * p[0];
    use = tout < s[2] ? tout : s[2];
    s[2] -= use; s[3] += (tout - use) * p[1];
  }
  const totals = new Map();
  for (const s of pairs.values()) {
    const p = prices.get(s[1]);
    totals.set(s[0], (totals.get(s[0]) || 0) + p[2] + (s[3] < p[4] ? s[3] : p[4]));
  }
  const users = [...totals.keys()].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  return users.map((u) => [u, totals.get(u)]);
}

function calculateMonthlySpend(sessions, pricing) { return solve(sessions, pricing); }

module.exports = solve;
module.exports.calculateMonthlySpend = calculateMonthlySpend;
