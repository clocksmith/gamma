'use strict';

// 2216. Minimum Deletions to Make Array Beautiful: greedily complete unequal pairs and remove any unmatched final element.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(nums) {
  let kept = 0;
  let deleted = 0;
  let previous = 0;
  for (const value of nums) {
    if (kept % 2 && value === previous) deleted += 1;
    else {
      kept += 1;
      previous = value;
    }
  }
  return deleted + kept % 2;
}

const minDeletion = solve;
class Solution {
  minDeletion(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDeletion };
