"use strict";
// Hack2Hire 68799c22ef2889afac734164 (Food Delivery System, variant 1 of 2) over an INFERRED spec; qualification unknown.

class FoodDeliverySystem {
  constructor(restaurants, menu) {
    const location = new Map();
    for (const row of restaurants) location.set(row[0], row);
    this.cheapest = new Map();
    this.xs = new Map(); // item -> x coordinates of the restaurants offering it
    this.ys = new Map();
    for (const [rid, item, price] of menu) {
      if (!this.cheapest.has(item) || price < this.cheapest.get(item)) this.cheapest.set(item, price);
      if (!this.xs.has(item)) { this.xs.set(item, []); this.ys.set(item, []); }
      const row = location.get(rid);
      this.xs.get(item).push(row[1]);
      this.ys.get(item).push(row[2]);
    }
  }

  getBestOption(item, userX, userY) {
    const xs = this.xs.get(item);
    if (xs === undefined) return [-1, -1];
    const ys = this.ys.get(item);
    let fastest = Infinity;
    for (let i = 0; i < xs.length; i++) {
      const t = Math.abs(xs[i] - userX) + Math.abs(ys[i] - userY);
      if (t < fastest) fastest = t;
    }
    return [this.cheapest.get(item), fastest];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "FoodDeliverySystem" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new FoodDeliverySystem(...argumentLists[0]);
  const allowed = new Set(["getBestOption"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.FoodDeliverySystem = FoodDeliverySystem;
