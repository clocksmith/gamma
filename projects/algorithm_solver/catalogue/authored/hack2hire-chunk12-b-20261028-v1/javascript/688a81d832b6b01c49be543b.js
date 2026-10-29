"use strict";
// Hack2Hire 688a81d832b6b01c49be543b (Minimal Difference in Two Arrays) over an INFERRED spec; qualification unknown.

function solve(A, B) {
  let i = 0, j = 0, best = Math.abs(A[0] - B[0]);
  while (i < A.length && j < B.length && best > 0) {
    const d = A[i] - B[j];
    if (Math.abs(d) < best) best = Math.abs(d);
    if (d < 0) i++; else j++;
  }
  let low = 0, high = 0;
  for (const a of A) {
    while (low < B.length && B[low] < a - best) low++;
    if (low < B.length && B[low] === a - best) return [a, a - best];
    while (high < B.length && B[high] < a + best) high++;
    if (high < B.length && B[high] === a + best) return [a, a + best];
  }
  throw new Error("minimum difference not found");
}

function findMinAbsDiffPair(A, B) { return solve(A, B); }

module.exports = solve;
module.exports.findMinAbsDiffPair = findMinAbsDiffPair;
