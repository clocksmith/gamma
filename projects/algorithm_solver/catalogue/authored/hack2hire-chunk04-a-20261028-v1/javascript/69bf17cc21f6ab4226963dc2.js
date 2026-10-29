"use strict";
// Hack2Hire 69bf17cc21f6ab4226963dc2 (ATM Queue) over an INFERRED spec; qualification unknown.

function solve(amounts, k) {
  const rounds = amounts.map((a) => Math.floor((a + k - 1) / k));
  const order = amounts.map((_, i) => i);
  order.sort((x, y) => rounds[x] - rounds[y] || x - y);
  return order.map((i) => i + 1);
}

function atmOrder(amounts, k) { return solve(amounts, k); }

module.exports = solve;
module.exports.atmOrder = atmOrder;
