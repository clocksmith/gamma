'use strict';

// 1481. Least Number of Unique Integers after K Removals: remove complete value groups in ascending frequency order.
// O(n + u log(u + 1)) expected time and O(u) auxiliary space for u distinct values; inputs are read-only.
function solve(arr, k) {
  const counts = new Map();
  for (const value of arr) counts.set(value, (counts.get(value) || 0) + 1);
  const frequencies = Array.from(counts.values()).sort((a, b) => a - b);
  let remaining = k;
  let unique = frequencies.length;
  for (const count of frequencies) {
    if (count > remaining) break;
    remaining -= count;
    unique -= 1;
  }
  return unique;
}

const findLeastNumOfUniqueInts = solve;
class Solution {
  findLeastNumOfUniqueInts(arr, k) { return solve(arr, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLeastNumOfUniqueInts };
