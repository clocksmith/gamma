"use strict";
// Hack2Hire 677b5ef978175fce2ecdfc12 (End Of Day Balance, variant 1 of 2) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

function solve(transactions) {
  const balance = new Map();
  for (const [payer, payee, amount] of transactions) {
    balance.set(payer, (balance.get(payer) || 0) - amount);
    balance.set(payee, (balance.get(payee) || 0) + amount);
  }
  return Array.from(balance.keys()).sort(cmp).map((party) => [party, balance.get(party)]);
}

function endOfDayBalance(transactions) { return solve(transactions); }

module.exports = solve;
module.exports.endOfDayBalance = endOfDayBalance;
