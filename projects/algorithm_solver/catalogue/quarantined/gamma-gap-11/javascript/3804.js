'use strict';

// 3804. Number of Centered Subarrays.
// O(n^2) expected time and O(n) auxiliary space; inputs are preserved.
function solve(nums) {
  let answer = 0;
  for (let left = 0; left < nums.length; left += 1) {
    let total = 0;
    const values = new Set();
    for (let right = left; right < nums.length; right += 1) {
      total += nums[right];
      values.add(nums[right]);
      if (values.has(total)) answer += 1;
    }
  }
  return answer;
}

const countCenteredSubarrays = solve;
class Solution {
  countCenteredSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCenteredSubarrays };
