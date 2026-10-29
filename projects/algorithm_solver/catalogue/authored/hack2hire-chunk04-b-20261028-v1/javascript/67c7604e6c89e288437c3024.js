"use strict";
// Hack2Hire 67c7604e6c89e288437c3024 (Cake Order Fulfillment Check) over an INFERRED spec; qualification unknown.

function solve(stock, orders) {
  let [a, b, c] = stock;
  const result = [];
  for (const [x, y, z] of orders) {
    const ok = x <= a && y <= b && z <= c;
    if (ok) { a -= x; b -= y; c -= z; }
    result.push(ok);
  }
  return result;
}

function checkOrders(stock, orders) { return solve(stock, orders); }

module.exports = solve;
module.exports.checkOrders = checkOrders;
