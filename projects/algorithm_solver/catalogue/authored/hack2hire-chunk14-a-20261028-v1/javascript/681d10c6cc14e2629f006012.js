"use strict";
// Hack2Hire 681d10c6cc14e2629f006012 (Top K Pins) over an INFERRED spec; qualification unknown.

class PinManager {
  constructor() {
    this.byType = new Map();
  }

  addPin(pinId, score, pinType) {
    let list = this.byType.get(pinType);
    if (!list) { list = []; this.byType.set(pinType, list); }
    let lo = 0, hi = list.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      const e = list[mid];
      if (e[0] > score || (e[0] === score && e[1] < pinId)) lo = mid + 1; else hi = mid;
    }
    list.splice(lo, 0, [score, pinId]);
  }

  getTopK(pinType, k) {
    const list = this.byType.get(pinType) || [];
    return list.slice(0, k).map((e) => e[1]);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "PinManager" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new PinManager(...argumentLists[0]);
  const allowed = new Set(["addPin", "getTopK"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.PinManager = PinManager;
