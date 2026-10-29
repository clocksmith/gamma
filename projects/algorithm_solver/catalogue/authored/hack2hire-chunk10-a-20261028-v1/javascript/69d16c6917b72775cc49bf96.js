"use strict";
// Hack2Hire 69d16c6917b72775cc49bf96 (Design Ring Buffer) over an INFERRED spec; qualification unknown.

class RingBuffer {
  constructor(capacity) {
    this.capacity = capacity;
    this.cells = new Array(capacity).fill("");
    this.writePos = 0; this.readPos = 0; this.unread = 0;
  }

  write(data) {
    const cap = this.capacity, m = data.length;
    let start = this.writePos, from = 0;
    if (m > cap) { start = (start + m - cap) % cap; from = m - cap; } // only the last cap characters survive
    for (let i = from, c = start; i < m; i++) { this.cells[c] = data[i]; c = c + 1 === cap ? 0 : c + 1; }
    this.writePos = (this.writePos + m) % cap;
    this.unread = Math.min(cap, this.unread + m); // the read pointer never moves on overwrite
  }

  read(n) {
    const m = Math.min(n, this.unread), first = Math.min(m, this.capacity - this.readPos);
    const out = this.cells.slice(this.readPos, this.readPos + first).join("") + this.cells.slice(0, m - first).join("");
    this.readPos = (this.readPos + m) % this.capacity;
    this.unread -= m;
    return out;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RingBuffer" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new RingBuffer(...argumentLists[0]);
  const allowed = new Set(["write", "read"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.RingBuffer = RingBuffer;
