'use strict';

// 702. Search in a Sorted Array of Unknown Size. Use the supplied ArrayReader.get API and its out-of-range sentinel, without requiring a length.

function solve(reader, target) {
  let low = 0, high = 1;
  while (reader.get(high) < target) { low = high + 1; high *= 2; }
  while (low <= high) {
    const middle = Math.floor((low + high) / 2), value = reader.get(middle);
    if (value === target) return middle;
    if (value < target) low = middle + 1; else high = middle - 1;
  }
  return -1;
}

const search = solve;
class Solution {
  search(reader, target) { return solve(reader, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, search };
