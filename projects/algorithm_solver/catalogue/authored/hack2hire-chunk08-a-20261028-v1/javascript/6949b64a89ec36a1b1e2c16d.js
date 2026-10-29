"use strict";
// Hack2Hire 6949b64a89ec36a1b1e2c16d (Reconstruct Billing Status, variant 3 of 3) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(transactions) {
  const ordered = transactions.map((row) => [Number(row[4]), row[0], row]);
  ordered.sort((a, b) => a[0] - b[0] || cmp(a[1], b[1]));
  const balance = new Map(), peak = new Map();
  for (const [, , row] of ordered) {
    const user = row[1];
    const value = (balance.get(user) || 0) + (row[2] === "" ? 0 : Number(row[2])) - (row[3] === "" ? 0 : Number(row[3]));
    balance.set(user, value);
    if (value > (peak.get(user) || 0)) peak.set(user, value);
  }
  return Array.from(balance.keys()).sort(cmp).map((user) => [user, balance.get(user), peak.get(user) || 0]);
}

function billingHistory(transactions) { return solve(transactions); }

module.exports = solve;
module.exports.billingHistory = billingHistory;
