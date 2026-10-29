"use strict";
// Hack2Hire 6768c33400d569e371e007ec (High Correlation Seller); INFERRED spec; qualification unknown.
function cmpStr(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
function solve(records) {
  const pairs = new Map(), stores = new Set();
  const bump = (a, b) => { let row = pairs.get(a); if (!row) pairs.set(a, row = new Map()); row.set(b, (row.get(b) || 0) + 1); };
  for (const record of records) {
    const session = [...new Set(record)].sort(cmpStr);
    for (const s of session) stores.add(s);
    for (let i = 0; i < session.length; i++) for (let j = i + 1; j < session.length; j++) { bump(session[i], session[j]); bump(session[j], session[i]); }
  }
  return [...stores].sort(cmpStr).map(store => {
    const row = pairs.get(store) || new Map();
    let best = 0;
    for (const c of row.values()) if (c > best) best = c;
    const assoc = [];
    if (best > 0) for (const [s, c] of row) if (c === best) assoc.push(s);
    return [store, assoc.sort(cmpStr)];
  });
}
function highCorrelationSellers(records) { return solve(records); }
module.exports = solve;
module.exports.highCorrelationSellers = highCorrelationSellers;
