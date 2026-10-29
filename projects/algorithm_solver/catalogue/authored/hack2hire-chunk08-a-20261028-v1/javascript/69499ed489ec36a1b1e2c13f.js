"use strict";
// Hack2Hire 69499ed489ec36a1b1e2c13f (Reconstruct Billing Status, variant 1 of 3) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(transactions) {
  const balance = new Map();
  for (const [, user, charge, payment] of transactions) {
    balance.set(user, (balance.get(user) || 0) + (charge === "" ? 0 : Number(charge)) - (payment === "" ? 0 : Number(payment)));
  }
  return Array.from(balance.keys()).sort(cmp).map((user) => [user, balance.get(user)]);
}

function reconstructBilling(transactions) { return solve(transactions); }

module.exports = solve;
module.exports.reconstructBilling = reconstructBilling;
