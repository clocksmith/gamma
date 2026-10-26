'use strict';

// 2453. Destroy Sequential Targets: choose the smallest target in a largest residue class.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums, space) {
  const counts = new Map();
  for (const value of nums) {
    const residue = value % space;
    counts.set(residue, (counts.get(residue) || 0) + 1);
  }
  let answer = nums[0];
  let bestCount = 0;
  for (const value of nums) {
    const count = counts.get(value % space);
    if (count > bestCount || (count === bestCount && value < answer)) {
      answer = value;
      bestCount = count;
    }
  }
  return answer;
}

const destroyTargets = solve;
class Solution {
  destroyTargets(nums, space) { return solve(nums, space); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, destroyTargets };
