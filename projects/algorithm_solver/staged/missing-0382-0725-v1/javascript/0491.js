'use strict';

// 491. Non-decreasing Subsequences.

function solve(nums) {
  const answer = [], path = [];
  function search(start) {
    if (path.length >= 2) answer.push(path.slice());
    const used = new Set();
    for (let i = start; i < nums.length; i += 1) {
      const value = nums[i];
      if (used.has(value) || (path.length > 0 && value < path[path.length - 1])) continue;
      used.add(value); path.push(value); search(i + 1); path.pop();
    }
  }
  search(0);
  return answer;
}

const findSubsequences = solve;
class Solution {
  findSubsequences(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSubsequences };
