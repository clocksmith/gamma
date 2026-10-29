"use strict";
// Hack2Hire 6917944e10632c00111ca217 (Delivery Cost Calculate, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
// scaled = sum of rateCents * seconds stays below 2**53 within the inferred bounds, so Number arithmetic is exact.
function money(scaled) {
  const twice = 2 * scaled + 3600, cents = (twice - twice % 7200) / 7200;
  return Math.floor(cents / 100) + "." + String(cents % 100).padStart(2, "0");
}
class MinHeap {
  constructor() { this.items = []; }
  get size() { return this.items.length; }
  peek() { return this.items[0]; }
  push(item) {
    const a = this.items;
    a.push(item);
    for (let i = a.length - 1; i > 0;) {
      const parent = (i - 1) >> 1;
      if (a[parent][0] <= a[i][0]) break;
      [a[parent], a[i]] = [a[i], a[parent]];
      i = parent;
    }
  }
  pop() {
    const a = this.items, top = a[0], last = a.pop();
    if (a.length) {
      a[0] = last;
      for (let i = 0; ;) {
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < a.length && a[l][0] < a[m][0]) m = l;
        if (r < a.length && a[r][0] < a[m][0]) m = r;
        if (m === i) break;
        [a[m], a[i]] = [a[i], a[m]];
        i = m;
      }
    }
    return top;
  }
}
class DeliverySystem {
  constructor() {
    this.rates = new Map();
    this.total = 0;
    this.unpaid = 0;
    this.unpaidHeap = new MinHeap();
  }
  addDriver(driverId, hourlyRateCents) { this.rates.set(driverId, hourlyRateCents); }
  addDelivery(driverId, startTime, endTime) {
    const scaled = this.rates.get(driverId) * (endTime - startTime);
    this.total += scaled;
    this.unpaid += scaled;
    this.unpaidHeap.push([endTime, scaled]);
  }
  getTotalCost() { return money(this.total); }
  payUpTo(upToTime) {
    while (this.unpaidHeap.size && this.unpaidHeap.peek()[0] <= upToTime) this.unpaid -= this.unpaidHeap.pop()[1];
  }
  getTotalCostUnpaid() { return money(this.unpaid); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "DeliverySystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new DeliverySystem(...argumentLists[0]), allowed = new Set(["addDriver", "addDelivery", "getTotalCost", "payUpTo", "getTotalCostUnpaid"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.DeliverySystem = DeliverySystem;
