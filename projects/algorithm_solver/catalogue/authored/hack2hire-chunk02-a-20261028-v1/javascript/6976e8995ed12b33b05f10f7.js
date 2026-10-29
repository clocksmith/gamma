"use strict";
// Hack2Hire 6976e8995ed12b33b05f10f7 (Match Payment to Invoice, v2); INFERRED spec; qualification unknown.
const MARKER = 'paying off:';
function cmpStr(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
function isIdChar(ch) { return /^[A-Za-z0-9_-]$/.test(ch); }
function referenceId(memo) {
  const at = memo.indexOf(MARKER);
  if (at < 0) return null;
  let end = at + MARKER.length;
  while (end < memo.length && isIdChar(memo[end])) end++;
  return end > at + MARKER.length ? memo.slice(at + MARKER.length, end) : null;
}
function splitPayment(record) {
  const a = record.indexOf(','), b = record.indexOf(',', a + 1);
  return [record.slice(0, a), record.slice(a + 1, b), record.slice(b + 1)];
}
function solve(payments, invoices) {
  const parsed = invoices.map(r => r.split(','));
  const known = new Set(parsed.map(p => p[0])), buckets = new Map();
  for (const [id, amount] of parsed.slice().sort((x, y) => cmpStr(x[2], y[2]) || cmpStr(x[0], y[0]))) {
    const key = Number(amount);
    if (!buckets.has(key)) buckets.set(key, {ids: [], next: 0});
    buckets.get(key).ids.push(id);
  }
  const used = new Set(), out = [];
  for (const record of payments) {
    const [paymentId, amount, memo] = splitPayment(record), target = referenceId(memo);
    let match = null;
    if (target !== null && known.has(target) && !used.has(target)) match = target;
    else {
      const bucket = buckets.get(Number(amount));
      if (bucket) {
        while (bucket.next < bucket.ids.length && used.has(bucket.ids[bucket.next])) bucket.next++;
        if (bucket.next < bucket.ids.length) match = bucket.ids[bucket.next];
      }
    }
    if (match !== null) used.add(match);
    out.push([paymentId, match]);
  }
  return out;
}
function matchPayments(payments, invoices) { return solve(payments, invoices); }
module.exports = solve;
module.exports.matchPayments = matchPayments;
