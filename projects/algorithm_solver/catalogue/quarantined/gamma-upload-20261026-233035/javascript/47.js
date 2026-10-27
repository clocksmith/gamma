'use strict';
// 47. Permutations II.
function solve(nums) {
  nums = nums.slice().sort((a, b) => a - b);
  const used = Array(nums.length).fill(false);
  const result = [];
  const path = [];
  function visit() {
    if (path.length === nums.length) { result.push(path.slice()); return; }
    for (let index = 0; index < nums.length; index += 1) {
      if (used[index] || (index > 0 && nums[index - 1] === nums[index] && !used[index - 1])) continue;
      used[index] = true; path.push(nums[index]);
      visit();
      path.pop(); used[index] = false;
    }
  }
  visit();
  return result;
}
const permuteUnique = solve;
class Solution { permuteUnique(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, permuteUnique };
