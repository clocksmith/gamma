'use strict';
// 31. Next Permutation.
function solve(nums) {
  let pivot = nums.length - 2;
  while (pivot >= 0 && nums[pivot] >= nums[pivot + 1]) pivot -= 1;
  if (pivot >= 0) {
    let swap = nums.length - 1;
    while (nums[swap] <= nums[pivot]) swap -= 1;
    [nums[pivot], nums[swap]] = [nums[swap], nums[pivot]];
  }
  for (let left = pivot + 1, right = nums.length - 1; left < right; left += 1, right -= 1) {
    [nums[left], nums[right]] = [nums[right], nums[left]];
  }
}
const nextPermutation = solve;
class Solution { nextPermutation(nums) { solve(nums); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextPermutation };
