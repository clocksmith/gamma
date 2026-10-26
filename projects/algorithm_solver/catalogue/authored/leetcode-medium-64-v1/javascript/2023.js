'use strict';

// 2023. Number of Pairs of Strings With Concatenation Equal to Target: count ordered prefix-suffix pairs and exclude pairing an index with itself.
// O(S + L^2) expected time and O(S + L) space for S input characters and target length L; inputs are read-only.
function solve(nums, target) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  let answer = 0;
  for (let split = 1; split < target.length; split += 1) {
    const left = target.slice(0, split);
    const right = target.slice(split);
    const leftCount = counts.get(left) || 0;
    const rightCount = counts.get(right) || 0;
    answer += leftCount * rightCount;
    if (left === right) answer -= leftCount;
  }
  return answer;
}

const numOfPairs = solve;
class Solution {
  numOfPairs(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfPairs };
