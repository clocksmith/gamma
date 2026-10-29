"use strict";
// Hack2Hire 69445eb8867a3f9f539ff53d (Customer Revenue System, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
function lowerBound(ranked, total, id) {
  let lo = 0, hi = ranked.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1, [t, i] = ranked[mid];
    if (t < total || (t === total && i < id)) lo = mid + 1; else hi = mid;
  }
  return lo;
}
class CustomerRevenueSystem {
  constructor() {
    this.own = [];
    this.total = [];
    this.children = [];
    this.ranked = []; // sorted [total, id]
  }
  add(revenue) {
    const customer = this.own.length;
    this.own.push(revenue);
    this.total.push(revenue);
    this.children.push([]);
    this.ranked.splice(lowerBound(this.ranked, revenue, customer), 0, [revenue, customer]);
    return customer;
  }
  insert(revenue) { return this.add(revenue); }
  insertWithReferrer(revenue, referrerId) {
    const customer = this.add(revenue);
    this.children[referrerId].push(customer);
    this.ranked.splice(lowerBound(this.ranked, this.total[referrerId], referrerId), 1);
    this.total[referrerId] += revenue;
    this.ranked.splice(lowerBound(this.ranked, this.total[referrerId], referrerId), 0, [this.total[referrerId], referrerId]);
    return customer;
  }
  getLowestK(k, minTotal) {
    const start = lowerBound(this.ranked, minTotal, -1);
    return this.ranked.slice(start, start + k).map(e => e[1]);
  }
  getNestedRevenue(customerId, maxDepth) {
    const queue = [customerId], depths = [0];
    let total = 0;
    for (let head = 0; head < queue.length; head++) {
      const customer = queue[head], depth = depths[head];
      total += this.own[customer];
      if (depth < maxDepth) for (const child of this.children[customer]) { queue.push(child); depths.push(depth + 1); }
    }
    return total;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "CustomerRevenueSystem") throw new Error("exact initial constructor required");
  const instance = new CustomerRevenueSystem(...argumentLists[0]);
  const allowed = new Set(["insert", "insertWithReferrer", "getLowestK", "getNestedRevenue"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.CustomerRevenueSystem = CustomerRevenueSystem;
