"use strict";
// Hack2Hire 6a1a0a79c81f779dc6a23756 (Credit Card Fraud Detection, variant 2 of 3) over an INFERRED spec; qualification unknown.

function solve(requests, rules) {
  const cards = new Set(), merchants = new Set();
  let limit = Infinity;
  for (const rule of rules) {
    const [field, value] = rule.split(',');
    if (field === 'card_number') cards.add(value);
    else if (field === 'merchant') merchants.add(value);
    else if (Number(value) < limit) limit = Number(value);
  }
  const parsed = requests.map((s) => { const f = s.split(','); return [Number(f[0]), f[1], Number(f[2]), f[3], f[4]]; });
  parsed.sort((x, y) => x[0] - y[0]);  // stable
  return parsed.map(([, uid, amount, card, merchant]) => [uid, cards.has(card) || merchants.has(merchant) || amount > limit ? 'DECLINE' : 'APPROVE']);
}

function processRequests(requests, rules) { return solve(requests, rules); }

module.exports = solve;
module.exports.processRequests = processRequests;
