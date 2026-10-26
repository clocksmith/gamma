'use strict';

// 3741. Minimum Distance Between Three Equal Elements II.
// O(n) expected time and O(n) space; the best triple consists of consecutive occurrences.
function solve(nums) {
  const recent = new Map();
  let answer = Infinity;
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index];
    const [first, second] = recent.get(value) || [-1, -1];
    if (first >= 0) answer = Math.min(answer, 2 * (index - first));
    recent.set(value, [second, index]);
  }
  return answer === Infinity ? -1 : answer;
}

const minimumDistance = solve;
class Solution {
  minimumDistance(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDistance };
