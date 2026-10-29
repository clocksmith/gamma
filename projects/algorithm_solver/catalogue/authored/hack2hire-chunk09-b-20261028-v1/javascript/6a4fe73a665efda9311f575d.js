"use strict";
// Hack2Hire 6a4fe73a665efda9311f575d (Count Maximum Borrowing Days) over an INFERRED spec; qualification unknown.

function solve(lend, payback) {
  const n = lend.length;
  if (n === 0) return 0;
  // bit b is the lender with the b-th smallest payback
  const order = Array.from({length: n}, (_, i) => i).sort((x, y) => payback[x] - payback[y]);
  const a = order.map((i) => lend[i]), b = order.map((i) => payback[i]);
  const succ = new Int32Array(n);
  for (let i = 0; i < n; i++) {
    let mask = 0;
    for (let j = 0; j < n; j++) if (a[j] >= b[i]) mask |= 1 << j;
    succ[i] = mask;
  }
  const full = 1 << n, reach = new Int32Array(full);
  for (let i = 0; i < n; i++) reach[1 << i] = 1 << i;
  let best = 1;
  for (let mask = 1; mask < full; mask++) {
    const r = reach[mask];
    if (!r) continue;
    let size = 0;
    for (let m = mask; m; m &= m - 1) size++;
    if (size > best) best = size;
    // the union of successors of every possible last lender is the successors of the one with the smallest payback
    let next = succ[31 - Math.clz32(r & -r)] & ~mask;
    while (next) {
      const bit = next & -next;
      reach[mask | bit] |= bit;
      next ^= bit;
    }
  }
  return best;
}

function maxBorrowingDays(lend, payback) { return solve(lend, payback); }

module.exports = solve;
module.exports.maxBorrowingDays = maxBorrowingDays;
