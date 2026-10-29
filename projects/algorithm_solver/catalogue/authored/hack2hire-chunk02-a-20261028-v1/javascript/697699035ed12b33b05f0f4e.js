"use strict";
// Hack2Hire 697699035ed12b33b05f0f4e (Match Payment to Invoice, v1); INFERRED spec; qualification unknown.
const MARKER = 'paying off:';
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
  const known = new Set(invoices.map(r => r.slice(0, r.indexOf(','))));
  return payments.map(record => {
    const [paymentId, , memo] = splitPayment(record), target = referenceId(memo);
    return [paymentId, target !== null && known.has(target) ? target : null];
  });
}
function matchPaymentsByMemo(payments, invoices) { return solve(payments, invoices); }
module.exports = solve;
module.exports.matchPaymentsByMemo = matchPaymentsByMemo;
