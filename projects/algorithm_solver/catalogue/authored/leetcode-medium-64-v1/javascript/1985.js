'use strict';

// 1985. Find the Kth Largest Integer in the Array: sort decimal strings by length then lexical value without numeric conversion.
// O(n * L * log n) time and O(n) auxiliary space for maximum digit length L; inputs are read-only.
function solve(nums, k) {
  const ordered = [...nums].sort((left, right) => {
    if (left.length !== right.length) return left.length - right.length;
    return left < right ? -1 : left > right ? 1 : 0;
  });
  return ordered[ordered.length - k];
}

const kthLargestNumber = solve;
class Solution {
  kthLargestNumber(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthLargestNumber };
