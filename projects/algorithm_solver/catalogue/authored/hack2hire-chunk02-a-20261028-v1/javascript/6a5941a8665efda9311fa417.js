"use strict";
// Hack2Hire 6a5941a8665efda9311fa417 (Live Fraud Detector, v1); INFERRED spec; qualification unknown.
class DistinctPIIValuesCounter {
  constructor() { this.seen = new Set(); }
  processEvent(event) { for (let f = 1; f < 5; f++) if (event[f] !== '') this.seen.add(f + '\u0000' + event[f]); }
  getDistinctPIICount() { return this.seen.size; }
}
function solve(operations, args) {
  const receiver = new DistinctPIIValuesCounter(...args[0]), out = [null];
  for (let i = 1; i < operations.length; i++) { const v = receiver[operations[i]](...args[i]); out.push(v === undefined ? null : v); }
  return out;
}
module.exports = solve;
module.exports.DistinctPIIValuesCounter = DistinctPIIValuesCounter;
