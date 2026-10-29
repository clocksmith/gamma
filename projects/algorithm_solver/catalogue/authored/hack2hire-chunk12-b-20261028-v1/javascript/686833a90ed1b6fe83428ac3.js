"use strict";
// Hack2Hire 686833a90ed1b6fe83428ac3 (Minimize Cost with Vouchers) over an INFERRED spec; qualification unknown.

function solve(price, vouchersCount) {
  const heap = price.slice();
  const n = heap.length;
  let total = 0;
  for (const p of price) total += p;
  const down = (start) => {
    let i = start;
    const value = heap[i];
    for (;;) {
      let c = 2 * i + 1;
      if (c >= n) break;
      if (c + 1 < n && heap[c + 1] > heap[c]) c++;
      if (heap[c] <= value) break;
      heap[i] = heap[c];
      i = c;
    }
    heap[i] = value;
  };
  for (let i = (n >> 1) - 1; i >= 0; i--) down(i);
  for (let v = 0; v < vouchersCount; v++) {
    if (n === 0 || heap[0] === 0) break;
    const top = heap[0];
    const half = Math.floor(top / 2);
    total -= top - half;
    heap[0] = half;
    down(0);
  }
  return total;
}

function minimizeCost(price, vouchersCount) { return solve(price, vouchersCount); }

module.exports = solve;
module.exports.minimizeCost = minimizeCost;
