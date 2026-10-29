"use strict";
// Hack2Hire 67730b5ddd9437f8aa275b04 (Write Disk Block With Cycle) over an INFERRED spec; qualification unknown.

// min-heap of blocks keyed by (remaining writes, block id) over blocks that can still be written
function lessThan(left, ids, a, b) {
  return left[a] < left[b] || (left[a] === left[b] && ids[a] < ids[b]);
}

class DiskBlockManager {
  constructor(n, maximumCycles) {
    this.left = new Array(n).fill(maximumCycles);
    this.ids = Array.from({ length: n }, (_, i) => i);
    this.size = n; // ids in increasing order with equal keys already form a heap
  }

  swap(a, b) {
    const l = this.left[a]; this.left[a] = this.left[b]; this.left[b] = l;
    const d = this.ids[a]; this.ids[a] = this.ids[b]; this.ids[b] = d;
  }

  siftDown(i) {
    for (;;) {
      const l = 2 * i + 1;
      const r = l + 1;
      let m = i;
      if (l < this.size && lessThan(this.left, this.ids, l, m)) m = l;
      if (r < this.size && lessThan(this.left, this.ids, r, m)) m = r;
      if (m === i) return;
      this.swap(i, m);
      i = m;
    }
  }

  write() {
    if (this.size === 0) return -1;
    const block = this.ids[0];
    if (this.left[0] === 1) {
      this.size--;
      this.left[0] = this.left[this.size];
      this.ids[0] = this.ids[this.size];
      this.left.pop();
      this.ids.pop();
    } else {
      this.left[0]--;
    }
    this.siftDown(0);
    return block;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "DiskBlockManager" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new DiskBlockManager(...argumentLists[0]);
  const allowed = new Set(["write"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.DiskBlockManager = DiskBlockManager;
