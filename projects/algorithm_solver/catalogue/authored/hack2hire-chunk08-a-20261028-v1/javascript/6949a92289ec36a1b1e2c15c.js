"use strict";
// Hack2Hire 6949a92289ec36a1b1e2c15c (Reconstruct Billing Status, variant 2 of 3) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(transactions, timestamp) {
  const balance = new Map();
  for (const [, user, charge, payment, when] of transactions) {
    if (Number(when) > timestamp) continue;
    balance.set(user, (balance.get(user) || 0) + (charge === "" ? 0 : Number(charge)) - (payment === "" ? 0 : Number(payment)));
  }
  return Array.from(balance.keys()).sort(cmp).map((user) => [user, balance.get(user)]);
}

function billingStatusAt(transactions, timestamp) { return solve(transactions, timestamp); }

module.exports = solve;
module.exports.billingStatusAt = billingStatusAt;
