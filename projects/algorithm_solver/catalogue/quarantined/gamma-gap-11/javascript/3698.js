'use strict';

// 3698. Split Array With Minimum Difference.
// O(n) time and O(n) auxiliary space; both subarrays must be nonempty.
function solve(nums) {
  const n = nums.length;
  const suffix = new Uint8Array(n);
  suffix[n - 1] = 1;
  let total = 0;
  for (const value of nums) total += value;
  for (let index = n - 2; index >= 0; index -= 1) {
    suffix[index] = suffix[index + 1] && nums[index] > nums[index + 1] ? 1 : 0;
  }
  let leftSum = 0;
  let increasing = true;
  let answer = Infinity;
  for (let index = 0; index + 1 < n; index += 1) {
    leftSum += nums[index];
    if (index > 0 && nums[index - 1] >= nums[index]) increasing = false;
    if (increasing && suffix[index + 1]) answer = Math.min(answer, Math.abs(2 * leftSum - total));
  }
  return answer === Infinity ? -1 : answer;
}

const splitArray = solve;
class Solution {
  splitArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, splitArray };
