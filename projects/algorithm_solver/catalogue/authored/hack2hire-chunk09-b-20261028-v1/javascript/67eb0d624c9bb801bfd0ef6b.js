"use strict";
// Hack2Hire 67eb0d624c9bb801bfd0ef6b (Candlestick Data Generator) over an INFERRED spec; qualification unknown.

function solve(prices) {
  const ordered = prices.slice().sort((x, y) => x[0] - y[0]);
  const out = [];
  let current = null;
  for (const [time, price] of ordered) {
    const start = time - (time % 10);
    if (current === null || current[0] !== start) {
      current = [start, price, price, price, price];
      out.push(current);
    } else {
      if (price > current[1]) current[1] = price;
      if (price < current[2]) current[2] = price;
      current[4] = price;
    }
  }
  return out;
}

function generateCandlesticks(prices) { return solve(prices); }

module.exports = solve;
module.exports.generateCandlesticks = generateCandlesticks;
