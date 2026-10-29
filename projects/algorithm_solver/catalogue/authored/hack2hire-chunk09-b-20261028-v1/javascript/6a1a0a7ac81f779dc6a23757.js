"use strict";
// Hack2Hire 6a1a0a7ac81f779dc6a23757 (Credit Card Fraud Detection, variant 3 of 3) over an INFERRED spec; qualification unknown.

function solve(requests, rules, fraudReports) {
  const cards = new Set(), merchants = new Set();
  let limit = Infinity;
  for (const rule of rules) {
    const [field, value] = rule.split(',');
    if (field === 'card_number') cards.add(value);
    else if (field === 'merchant') merchants.add(value);
    else if (Number(value) < limit) limit = Number(value);
  }
  const cardOf = new Map();
  const parsed = requests.map((s) => { const f = s.split(','); cardOf.set(f[1], f[3]); return [Number(f[0]), f[1], Number(f[2]), f[3], f[4]]; });
  const blockedAfter = new Map();
  for (const report of fraudReports) {
    const [ts, uid] = report.split(','), card = cardOf.get(uid), t = Number(ts);
    if (!blockedAfter.has(card) || t < blockedAfter.get(card)) blockedAfter.set(card, t);
  }
  parsed.sort((x, y) => x[0] - y[0]);  // stable
  return parsed.map(([ts, uid, amount, card, merchant]) => {
    const bad = cards.has(card) || merchants.has(merchant) || amount > limit || (blockedAfter.has(card) && ts > blockedAfter.get(card));
    return [uid, bad ? 'DECLINE' : 'APPROVE'];
  });
}

function processRequests(requests, rules, fraudReports) { return solve(requests, rules, fraudReports); }

module.exports = solve;
module.exports.processRequests = processRequests;
