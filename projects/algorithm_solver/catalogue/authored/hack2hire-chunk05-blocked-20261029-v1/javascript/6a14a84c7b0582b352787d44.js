"use strict";
// Hack2Hire 6a14a84c7b0582b352787d44 (Design Ambient Light Sensor System) over an INFERRED spec; qualification unknown.
// Sequential only: the inferred thread-safe, non-blocking contract is not modelled here.

const SLOTS = 1000001; // timestamps 0..1e6

class ALSWrapper {
  constructor() {
    this.counts = new Map();
    this.sums = new Map();
    this.latest = null;
  }

  record(status, lux, timestamp) {
    if (status !== 1) return;
    for (let i = timestamp + 1; i <= SLOTS; i += i & -i) {
      this.counts.set(i, (this.counts.get(i) || 0) + 1);
      this.sums.set(i, (this.sums.get(i) || 0) + lux);
    }
    if (this.latest === null || timestamp >= this.latest[0]) this.latest = [timestamp, lux];
  }

  prefix(i) {
    let count = 0, total = 0;
    for (; i > 0; i -= i & -i) {
      count += this.counts.get(i) || 0;
      total += this.sums.get(i) || 0;
    }
    return [count, total];
  }

  getLatestLux() {
    return this.latest === null ? -1 : this.latest[1];
  }

  getAverageLux(startTime, endTime) {
    const [highCount, highTotal] = this.prefix(endTime + 1);
    const [lowCount, lowTotal] = this.prefix(startTime);
    const count = highCount - lowCount;
    if (count === 0) return -1;
    const total = highTotal - lowTotal;
    return (total - total % count) / count;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ALSWrapper" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new ALSWrapper();
  const allowed = new Set(["record", "getLatestLux", "getAverageLux"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ALSWrapper = ALSWrapper;
