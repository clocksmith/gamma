"use strict";
// Hack2Hire 6a5941f5665efda9311fa41e (Live Fraud Detector, v2); INFERRED spec; qualification unknown.
class DistinctPIIValuesCounter {
  constructor() { this.events = new Map(); this.shared = 0; }
  processEvent(event) {
    const keys = new Set();
    for (let f = 1; f < 5; f++) if (event[f] !== '') keys.add(f + '\u0000' + event[f]);
    for (const key of keys) {
      const count = (this.events.get(key) || 0) + 1;
      this.events.set(key, count);
      if (count === 2) this.shared++;
    }
  }
  getDistinctPIICount() { return this.events.size; }
  getSharedPIICount() { return this.shared; }
}
function solve(operations, args) {
  const receiver = new DistinctPIIValuesCounter(...args[0]), out = [null];
  for (let i = 1; i < operations.length; i++) { const v = receiver[operations[i]](...args[i]); out.push(v === undefined ? null : v); }
  return out;
}
module.exports = solve;
module.exports.DistinctPIIValuesCounter = DistinctPIIValuesCounter;
