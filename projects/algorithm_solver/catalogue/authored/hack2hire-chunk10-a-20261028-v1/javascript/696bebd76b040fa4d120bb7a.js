"use strict";
// Hack2Hire 696bebd76b040fa4d120bb7a (Design Squirrel Nut Tracker) over an INFERRED spec; qualification unknown.

// PREFIX[L] = total capacity of levels 0..L, with level capacities 1, 2, 3, 5, 8, ... (all below 2**53)
const PREFIX = [];
for (let a = 1, b = 2, total = 0; total <= 2e14; [a, b] = [b, a + b]) { total += a; PREFIX.push(total); }

class SquirrelResearch {
  constructor() { this.totals = new Map(); } // bottom-up filling and top-down removal keep the occupied levels a prefix

  _top(total) {
    if (total === 0) return -1;
    let lo = 0, hi = PREFIX.length;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (PREFIX[mid] < total) lo = mid + 1; else hi = mid; }
    return lo;
  }

  hideNuts(locationId, count) {
    const total = (this.totals.get(locationId) || 0) + count;
    this.totals.set(locationId, total);
    return this._top(total);
  }

  retrieveNuts(locationId, count) {
    const total = this.totals.get(locationId) || 0, take = Math.min(count, total);
    this.totals.set(locationId, total - take);
    return take;
  }

  getHighestLevel(locationId) { return this._top(this.totals.get(locationId) || 0); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SquirrelResearch" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new SquirrelResearch(...argumentLists[0]);
  const allowed = new Set(["hideNuts", "retrieveNuts", "getHighestLevel"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.SquirrelResearch = SquirrelResearch;
