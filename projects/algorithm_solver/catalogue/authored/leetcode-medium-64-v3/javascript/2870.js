'use strict';

// 2870. Minimum Number of Operations to Make Array Empty: split each frequency into groups of two and three.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  let answer = 0;
  for (const count of counts.values()) {
    if (count === 1) return -1;
    answer += Math.floor((count + 2) / 3);
  }
  return answer;
}

const minOperations = solve;
class Solution {
  minOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
