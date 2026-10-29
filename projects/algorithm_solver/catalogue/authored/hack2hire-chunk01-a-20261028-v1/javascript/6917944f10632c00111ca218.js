"use strict";
// Hack2Hire 6917944f10632c00111ca218 (Delivery Cost Calculate, variant 3) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
// scaled = sum of rateCents * seconds stays below 2**53 within the inferred bounds, so Number arithmetic is exact.
const SPAN = 2 ** 30; // time domain [0, 2**30) covers every inferred instant (<= 1e9)
class MaxTree { // dynamic segment tree: range add, range max; absent children hold zero
  constructor() { this.left = [-1]; this.right = [-1]; this.best = [0]; this.add = [0]; }
  child(node, side) {
    const links = side === 0 ? this.left : this.right;
    if (links[node] < 0) { links[node] = this.best.length; this.left.push(-1); this.right.push(-1); this.best.push(0); this.add.push(0); }
    return links[node];
  }
  update(low, high, delta, node = 0, lo = 0, hi = SPAN - 1) {
    if (low <= lo && hi <= high) { this.add[node] += delta; this.best[node] += delta; return; }
    const mid = Math.floor((lo + hi) / 2);
    if (low <= mid) this.update(low, high, delta, this.child(node, 0), lo, mid);
    if (high > mid) this.update(low, high, delta, this.child(node, 1), mid + 1, hi);
    const l = this.left[node], r = this.right[node];
    this.best[node] = this.add[node] + Math.max(l >= 0 ? this.best[l] : 0, r >= 0 ? this.best[r] : 0);
  }
  query(low, high, node = 0, lo = 0, hi = SPAN - 1) {
    if (node < 0) return 0;
    if (low <= lo && hi <= high) return this.best[node];
    const mid = Math.floor((lo + hi) / 2);
    let result = 0;
    if (low <= mid) result = this.query(low, high, this.left[node], lo, mid);
    if (high > mid) result = Math.max(result, this.query(low, high, this.right[node], mid + 1, hi));
    return this.add[node] + result;
  }
}
function lowerBound(a, x) { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] < x) lo = m + 1; else hi = m; } return lo; }
function upperBound(a, x) { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] <= x) lo = m + 1; else hi = m; } return lo; }
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
    this.unions = new Map(); // driver -> [starts, ends] of its disjoint merged delivery intervals
    this.coverage = new MaxTree(); // distinct active drivers per instant
  }
  addDriver(driverId, hourlyRateCents) { this.rates.set(driverId, hourlyRateCents); }
  addDelivery(driverId, startTime, endTime) {
    const scaled = this.rates.get(driverId) * (endTime - startTime);
    this.total += scaled;
    this.unpaid += scaled;
    this.unpaidHeap.push([endTime, scaled]);
    if (!this.unions.has(driverId)) this.unions.set(driverId, [[], []]);
    const [starts, ends] = this.unions.get(driverId);
    const first = lowerBound(ends, startTime), last = upperBound(starts, endTime); // touching unions merge
    let low = startTime, high = endTime;
    for (let k = first; k < last; k++) {
      this.coverage.update(starts[k], ends[k] - 1, -1);
      low = Math.min(low, starts[k]); high = Math.max(high, ends[k]);
    }
    starts.splice(first, last - first, low);
    ends.splice(first, last - first, high);
    this.coverage.update(low, high - 1, 1);
  }
  getTotalCost() { return money(this.total); }
  payUpTo(upToTime) {
    while (this.unpaidHeap.size && this.unpaidHeap.peek()[0] <= upToTime) this.unpaid -= this.unpaidHeap.pop()[1];
  }
  getTotalCostUnpaid() { return money(this.unpaid); }
  getMaxActiveDriversInLast24Hours(currentTime) {
    return this.coverage.query(Math.max(currentTime - 86400, 0), currentTime);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "DeliverySystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new DeliverySystem(...argumentLists[0]), allowed = new Set(["addDriver", "addDelivery", "getTotalCost", "payUpTo", "getTotalCostUnpaid", "getMaxActiveDriversInLast24Hours"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.DeliverySystem = DeliverySystem;
