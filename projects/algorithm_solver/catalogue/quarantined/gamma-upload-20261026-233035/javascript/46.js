'use strict';
// 46. Permutations.
function solve(nums) {
  const result = [];
  function visit(index) {
    if (index === nums.length) { result.push(nums.slice()); return; }
    for (let swap = index; swap < nums.length; swap += 1) {
      [nums[index], nums[swap]] = [nums[swap], nums[index]];
      visit(index + 1);
      [nums[index], nums[swap]] = [nums[swap], nums[index]];
    }
  }
  visit(0);
  return result;
}
const permute = solve;
class Solution { permute(nums) { return solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, permute };
