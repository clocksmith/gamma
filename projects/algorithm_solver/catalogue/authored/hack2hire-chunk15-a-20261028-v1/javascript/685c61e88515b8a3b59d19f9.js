"use strict";
// Hack2Hire 685c61e88515b8a3b59d19f9 (Bulk Fruit Order Discount) over an INFERRED spec; qualification unknown.

const WINDOW = 600000;

function groupCost(quantity, size, unit, tiers) {
  let percent = 0;
  if (size >= 2) {
    let lo = 0, hi = tiers.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (tiers[mid][0] <= quantity) lo = mid + 1; else hi = mid;
    }
    if (lo) percent = tiers[lo - 1][1];
  }
  const x = quantity * unit * (100 - percent);
  return (x - x % 100) / 100;
}

function solve(orders, prices, tiers) {
  const price = new Map();
  for (const [fruit, unit] of prices) price.set(fruit, unit);
  const byFruit = new Map();
  for (const [fruit, quantity, timestamp] of orders) {
    if (!byFruit.has(fruit)) byFruit.set(fruit, []);
    byFruit.get(fruit).push([Number(timestamp), Number(quantity)]);
  }
  let total = 0;
  for (const [fruit, items] of byFruit) {
    items.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const unit = price.get(fruit);
    let quantity = 0, size = 0, last = null;
    for (const [timestamp, amount] of items) {
      if (last !== null && timestamp - last > WINDOW) {
        total += groupCost(quantity, size, unit, tiers);
        quantity = 0; size = 0;
      }
      quantity += amount; size += 1; last = timestamp;
    }
    total += groupCost(quantity, size, unit, tiers);
  }
  return total;
}

function totalCost(orders, prices, tiers) { return solve(orders, prices, tiers); }

module.exports = solve;
module.exports.totalCost = totalCost;
