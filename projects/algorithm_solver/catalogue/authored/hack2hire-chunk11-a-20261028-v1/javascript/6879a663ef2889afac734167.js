"use strict";
// Hack2Hire 6879a663ef2889afac734167 (Food Delivery System, variant 2 of 2) over an INFERRED spec; qualification unknown.

function fastest(xs, ys, userX, userY) {
  let best = Infinity;
  for (let i = 0; i < xs.length; i++) {
    const t = Math.abs(xs[i] - userX) + Math.abs(ys[i] - userY);
    if (t < best) best = t;
  }
  return best;
}

class FoodDeliverySystem {
  constructor(restaurants, menu) {
    this.location = new Map();
    for (const row of restaurants) this.location.set(row[0], row);
    this.cheapest = new Map();
    this.offers = new Map(); // item -> Map(restaurant id -> price)
    this.xs = new Map();     // item -> x coordinates of the restaurants offering it
    this.ys = new Map();
    for (const [rid, item, price] of menu) {
      if (!this.cheapest.has(item) || price < this.cheapest.get(item)) this.cheapest.set(item, price);
      if (!this.offers.has(item)) { this.offers.set(item, new Map()); this.xs.set(item, []); this.ys.set(item, []); }
      this.offers.get(item).set(rid, price);
      const row = this.location.get(rid);
      this.xs.get(item).push(row[1]);
      this.ys.get(item).push(row[2]);
    }
    this.orders = new Map(); // sorted item key -> {best, xs, ys} of qualifying restaurants, or null; the menu never changes
  }

  getBestOption(item, userX, userY) {
    const xs = this.xs.get(item);
    if (xs === undefined) return [-1, -1];
    return [this.cheapest.get(item), fastest(xs, this.ys.get(item), userX, userY)];
  }

  order(items) {
    const maps = [];
    for (const item of items) {
      const offers = this.offers.get(item);
      if (offers === undefined) return null;
      maps.push(offers);
    }
    let rarest = maps[0];
    for (const offers of maps) if (offers.size < rarest.size) rarest = offers;
    let best = -1;
    const xs = [], ys = [];
    for (const rid of rarest.keys()) {
      let total = 0, all = true;
      for (let j = 0; j < maps.length; j++) {
        const price = maps[j].get(rid);
        if (price === undefined) { all = false; break; }
        total += price;
      }
      if (!all) continue;
      if (best < 0 || total < best) best = total;
      const row = this.location.get(rid);
      xs.push(row[1]);
      ys.push(row[2]);
    }
    return xs.length ? { best, xs, ys } : null;
  }

  getBestOrder(items, userX, userY) {
    const key = items.slice().sort().join(",");
    if (!this.orders.has(key)) this.orders.set(key, this.order(items));
    const found = this.orders.get(key);
    if (found === null) return [-1, -1];
    return [found.best, fastest(found.xs, found.ys, userX, userY)];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "FoodDeliverySystem" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new FoodDeliverySystem(...argumentLists[0]);
  const allowed = new Set(["getBestOption", "getBestOrder"]);
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
