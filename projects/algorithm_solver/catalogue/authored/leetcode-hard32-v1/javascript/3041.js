'use strict';

// 3041. Maximize Consecutive Elements in an Array After Modification.
// O(n log n) time, O(n) space. Sort a copy; do not reuse one element in both transitions.
function solve(nums) {
  const ordered = nums.slice().sort((a, b) => a - b);
  const longest = new Map();
  let answer = 0;
  for (const value of ordered) {
    const unchanged = (longest.get(value - 1) || 0) + 1;
    const increased = (longest.get(value) || 0) + 1;
    longest.set(value + 1, Math.max(longest.get(value + 1) || 0, increased));
    longest.set(value, Math.max(longest.get(value) || 0, unchanged));
    answer = Math.max(answer, longest.get(value), longest.get(value + 1));
  }
  return answer;
}

const maxSelectedElements = solve;
class Solution {
  maxSelectedElements(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSelectedElements };
