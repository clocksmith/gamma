'use strict';

// 2206. Divide Array Into Equal Pairs (Easy).
// Specification: https://leetcode.com/problems/divide-array-into-equal-pairs/description/
// O(n) expected time, O(n) space; every distinct value needs an even frequency.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  for (const count of counts.values()) {
    if (count % 2 !== 0) return false;
  }
  return true;
}

const divideArray = solve;
class Solution {
  divideArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, divideArray };
