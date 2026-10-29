// Original hack2hire:6a171a967b0582b3527890e5; inferred public-preview contract; qualification unknown.
"use strict";
class IPRangeIterator {
  constructor(start) { this.current = start.split('.').reduce((n, part) => n*256 + Number(part), 0); }
  hasNext() { return this.current < 4294967296; }
  next() {
    if (!this.hasNext()) return null;
    let value = this.current++; const parts = [];
    for (let i = 0; i < 4; i++) { parts.push(String(value % 256)); value = Math.floor(value/256); }
    return parts.reverse().join('.');
  }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "IPRangeIterator") throw new Error("exact constructor trace required");
  const instance = new IPRangeIterator(...argumentLists[0]), result = [null], allowed = new Set(["hasNext", "next"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.IPRangeIterator = IPRangeIterator;
