'use strict';

// 3043. Find the Length of the Longest Common Prefix: index integer prefixes of the first array and search the second from longest to shortest.
// O((n + m) * D) expected time and O(n * D) auxiliary space, where D is the maximum digit count; inputs are read-only.
function solve(arr1, arr2) {
  const prefixes = new Set();
  for (const number of arr1) {
    let value = number;
    while (value > 0) {
      prefixes.add(value);
      value = Math.floor(value / 10);
    }
  }
  let best = 0;
  for (const number of arr2) {
    let value = number;
    let length = String(number).length;
    while (value > 0) {
      if (prefixes.has(value)) {
        best = Math.max(best, length);
        break;
      }
      value = Math.floor(value / 10);
      length -= 1;
    }
  }
  return best;
}

const longestCommonPrefix = solve;
class Solution {
  longestCommonPrefix(arr1, arr2) { return solve(arr1, arr2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestCommonPrefix };
