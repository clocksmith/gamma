'use strict';

// 1299. Replace Elements with Greatest Element on Right Side (Easy).
// Specification: https://leetcode.com/problems/replace-elements-with-greatest-element-on-right-side/description/
// O(n) time, O(n) output space; preserve arr.
function solve(arr) {
  const result = new Array(arr.length);
  let greatest = -1;
  for (let index = arr.length - 1; index >= 0; index--) {
    result[index] = greatest;
    greatest = Math.max(greatest, arr[index]);
  }
  return result;
}

const replaceElements = solve;
class Solution {
  replaceElements(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, replaceElements };
