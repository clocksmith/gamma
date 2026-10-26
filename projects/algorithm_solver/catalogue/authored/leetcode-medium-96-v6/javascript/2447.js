'use strict';

// 2447. Number of Subarrays With GCD Equal to K: extend each starting point until its gcd can no longer be a multiple of k.
// O(n^2 log U) time and O(1) auxiliary space for maximum value U; inputs are read-only.
function solve(nums, k) {
  function gcd(left, right) {
    while (right !== 0) [left, right] = [right, left % right];
    return left;
  }
  let answer = 0;
  for (let left = 0; left < nums.length; left += 1) {
    let current = 0;
    for (let right = left; right < nums.length; right += 1) {
      current = gcd(current, nums[right]);
      if (current % k !== 0) break;
      if (current === k) answer += 1;
    }
  }
  return answer;
}

const subarrayGCD = solve;
class Solution {
  subarrayGCD(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subarrayGCD };
