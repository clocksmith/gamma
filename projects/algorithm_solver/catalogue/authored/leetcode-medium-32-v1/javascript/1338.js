'use strict';

// 1338. Reduce Array Size to The Half: remove the most frequent values first.
// O(n + u log u) time and O(u) auxiliary space for u distinct values; inputs are read-only.
function solve(arr) {
  const counts = new Map();
  for (const value of arr) counts.set(value, (counts.get(value) || 0) + 1);
  const frequencies = [...counts.values()].sort((left, right) => right - left);
  let removed = 0;
  for (let index = 0; index < frequencies.length; index += 1) {
    removed += frequencies[index];
    if (removed * 2 >= arr.length) return index + 1;
  }
  return 0;
}

const minSetSize = solve;
class Solution {
  minSetSize(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSetSize };
