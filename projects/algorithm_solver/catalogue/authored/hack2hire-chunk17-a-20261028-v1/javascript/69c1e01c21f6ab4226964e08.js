"use strict";
// Hack2Hire 69c1e01c21f6ab4226964e08 (Roadway Segment Speed Query) over an INFERRED spec; qualification unknown.

const SIZE = 1000002; // Fenwick indices 1 .. 1e6 + 1 for positions 0 .. 1e6

class RoadwaySpeedTracker {
  constructor() {
    this.sums = null;
    this.counts = null;
    this.live = new Map();
  }

  update(position, speed, count) {
    const sums = this.sums, counts = this.counts;
    for (let i = position + 1; i < SIZE; i += i & -i) {
      sums[i] += speed;
      counts[i] += count;
    }
  }

  addReport(start, end, speed) {
    if (this.sums === null) {
      this.sums = new Float64Array(SIZE);
      this.counts = new Int32Array(SIZE);
    }
    const key = start + "," + end + "," + speed;
    this.live.set(key, (this.live.get(key) || 0) + 1);
    this.update(start, speed, 1);
    this.update(end, -speed, -1);
  }

  removeReport(start, end, speed) {
    const key = start + "," + end + "," + speed;
    const copies = this.live.get(key) || 0;
    if (copies === 0) return false;
    if (copies === 1) this.live.delete(key);
    else this.live.set(key, copies - 1);
    this.update(start, -speed, -1);
    this.update(end, speed, 1);
    return true;
  }

  getAverageSpeed(point) {
    if (this.sums === null) return -1;
    const sums = this.sums, counts = this.counts;
    let total = 0, count = 0;
    for (let i = point + 1; i > 0; i -= i & -i) {
      total += sums[i];
      count += counts[i];
    }
    return count ? total / count : -1;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RoadwaySpeedTracker" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new RoadwaySpeedTracker(...argumentLists[0]);
  const allowed = new Set(["addReport", "removeReport", "getAverageSpeed"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.RoadwaySpeedTracker = RoadwaySpeedTracker;
