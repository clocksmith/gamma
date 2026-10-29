"use strict";
// Hack2Hire 68b996c98c4a0a9996afdd81 (Payment Refund Allocation) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
const RANK = new Map([["CREDIT", 0], ["CREDIT_CARD", 1], ["PAYPAL", 2]]);

function solve(transactions, refundAmount) {
  const refunded = new Map();
  for (const row of transactions) {
    if (row[1] === "REFUND") refunded.set(row[3], (refunded.get(row[3]) || 0) + Number(row[5]));
  }
  const payments = [];
  for (const row of transactions) {
    if (row[1] !== "PAYMENT") continue;
    const rank = RANK.has(row[2]) ? RANK.get(row[2]) : 3;
    payments.push([rank, rank === 3 ? row[2] : "", Number(row[4]), row[0], Number(row[5]) - (refunded.get(row[0]) || 0)]);
  }
  payments.sort((a, b) => a[0] - b[0] || cmp(a[1], b[1]) || b[2] - a[2] || cmp(a[3], b[3]));
  let remaining = refundAmount;
  const out = [];
  for (const p of payments) {
    if (remaining === 0) break;
    const give = p[4] < remaining ? p[4] : remaining;
    if (give > 0) { out.push([p[3], give]); remaining -= give; }
  }
  return out;
}

function allocateRefund(transactions, refundAmount) { return solve(transactions, refundAmount); }

module.exports = solve;
module.exports.allocateRefund = allocateRefund;
