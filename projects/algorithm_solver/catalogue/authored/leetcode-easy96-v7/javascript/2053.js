'use strict';

// 2053. Kth Distinct String in an Array (Easy).
// Specification: https://leetcode.com/problems/kth-distinct-string-in-an-array/description/
// O(total characters) expected time, O(n) map entries; retain original order and preserve arr.
function solve(arr, k) {
  const counts = new Map();
  for (const word of arr) counts.set(word, (counts.get(word) || 0) + 1);
  let remaining = k;
  for (const word of arr) {
    if (counts.get(word) !== 1) continue;
    remaining--;
    if (remaining === 0) return word;
  }
  return '';
}

const kthDistinct = solve;
class Solution {
  kthDistinct(arr, k) { return solve(arr, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthDistinct };
