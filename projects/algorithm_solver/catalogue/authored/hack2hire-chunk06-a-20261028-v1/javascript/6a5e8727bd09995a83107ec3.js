"use strict";
// Hack2Hire 6a5e8727bd09995a83107ec3 (Find Redeemable Offers) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(offers, events, processingTime) {
  const window = new Map();
  for (const [id, start, end, limit] of offers) window.set(id, [Number(start), Number(end), Number(limit)]);
  const counts = new Map(), users = new Set();
  for (const [user, timestamp, action, id] of events) {
    users.add(user);
    const info = window.get(id);
    if (info === undefined) continue;
    const t = Number(timestamp);
    if (t > processingTime || t < info[0] || t > info[1]) continue;
    const key = user + '\u0000' + id, count = counts.get(key) || 0;
    if (action === 'redeem') { if (count < info[2]) counts.set(key, count + 1); }
    else if (count > 0) counts.set(key, count - 1);
  }
  const active = [];
  for (const [id] of offers) { const info = window.get(id); if (info[0] <= processingTime && processingTime <= info[1]) active.push([id, info[2]]); }
  return Array.from(users).sort(cmp).map((user) => [user, active.filter(([id, limit]) => (counts.get(user + '\u0000' + id) || 0) < limit).map(([id]) => id)]);
}

function redeemableOffers(offers, events, processingTime) { return solve(offers, events, processingTime); }

module.exports = solve;
module.exports.redeemableOffers = redeemableOffers;
