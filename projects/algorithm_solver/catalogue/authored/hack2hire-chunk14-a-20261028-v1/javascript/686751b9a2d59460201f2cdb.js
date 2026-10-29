"use strict";
// Hack2Hire 686751b9a2d59460201f2cdb (Top K Book Sales) over an INFERRED spec; qualification unknown.

function before(negA, idA, negB, idB) { return negA < negB || (negA === negB && idA < idB); }

class BookSalesTracker {
  constructor() {
    this.totals = new Map();
    this.order = [];
  }

  position(neg, id) {
    let lo = 0, hi = this.order.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      const e = this.order[mid];
      if (before(e[0], e[1], neg, id)) lo = mid + 1; else hi = mid;
    }
    return lo;
  }

  recordSale(bookId, quantity) {
    const old = this.totals.get(bookId);
    if (old !== undefined) this.order.splice(this.position(-old, bookId), 1);
    const total = (old || 0) + quantity;
    this.totals.set(bookId, total);
    this.order.splice(this.position(-total, bookId), 0, [-total, bookId]);
  }

  getTopK(k) {
    return this.order.slice(0, k).map((e) => e[1]);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "BookSalesTracker" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new BookSalesTracker(...argumentLists[0]);
  const allowed = new Set(["recordSale", "getTopK"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.BookSalesTracker = BookSalesTracker;
