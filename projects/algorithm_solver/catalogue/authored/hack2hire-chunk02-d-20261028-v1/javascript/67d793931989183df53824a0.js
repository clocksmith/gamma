"use strict";
// Hack2Hire 67d793931989183df53824a0 (Fractional Inventory) over an INFERRED spec; qualification unknown.

function hundredths(text) {
  const dot = text.indexOf(".");
  if (dot < 0) return Number(text) * 100;
  return Number(text.slice(0, dot)) * 100 + Number((text.slice(dot + 1) + "00").slice(0, 2));
}

function floorDiv(a, b) {
  // exact floor for non-negative safe integers: correct any rounding of a / b
  let q = Math.floor(a / b);
  while (q * b > a) q--;
  while ((q + 1) * b <= a) q++;
  return q;
}

function solve(orders, inventory) {
  const held = new Map(inventory.map(([symbol, amount]) => [symbol, Number(amount)]));
  for (const [symbol, kind, quantity, price] of orders) {
    const amount = quantity[0] === "$" ? floorDiv(hundredths(quantity.slice(1)) * 100, Number(price)) : hundredths(quantity);
    let have = held.has(symbol) ? held.get(symbol) : 0;
    if (kind === "B") {
      if (have < amount) have += floorDiv(amount - have + 99, 100) * 100;
      have -= amount;
    } else {
      have = (have + amount) % 100;
    }
    held.set(symbol, have);
  }
  return [...held.keys()].sort().map((symbol) => [symbol, String(held.get(symbol))]);
}

function fractionalInventory(orders, inventory) { return solve(orders, inventory); }

module.exports = solve;
module.exports.fractionalInventory = fractionalInventory;
