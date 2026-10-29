"use strict";
// Hack2Hire 68b975348c4a0a9996afdd79 (Property Booking System) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

class BookingSystem {
  constructor(properties) {
    this.free = new Map(); // neighborhood -> [[id, capacity]] sorted by id
    for (const [pid, neighborhood, capacity] of properties) {
      if (!this.free.has(neighborhood)) this.free.set(neighborhood, []);
      this.free.get(neighborhood).push([pid, Number(capacity)]);
    }
    for (const props of this.free.values()) props.sort((a, b) => cmp(a[0], b[0]));
  }

  book(neighborhood, groupSize) {
    const props = this.free.get(neighborhood) || [];
    const caps = props.map((p) => p[1]).sort((a, b) => b - a);
    let size = 0, total = 0;
    while (size < caps.length && total < groupSize) total += caps[size++];
    if (total < groupSize) return [];
    const m = props.length, chosen = [];
    let best = null, bestSum = -1;
    const search = (start, need, subtotal) => {
      if (need === 0) {
        if (subtotal >= groupSize && (best === null || subtotal < bestSum)) { best = chosen.slice(); bestSum = subtotal; }
        return;
      }
      for (let i = start; i <= m - need; i++) {
        chosen.push(i);
        search(i + 1, need - 1, subtotal + props[i][1]);
        chosen.pop();
      }
    };
    search(0, size, 0);
    const picked = new Set(best);
    this.free.set(neighborhood, props.filter((_, i) => !picked.has(i)));
    return best.map((i) => props[i][0]);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "BookingSystem" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new BookingSystem(...argumentLists[0]);
  const allowed = new Set(["book"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.BookingSystem = BookingSystem;
