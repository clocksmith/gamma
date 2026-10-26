'use strict';

// 2470. Number of Subarrays With LCM Equal to K: extend each subarray while its least common multiple remains a divisor of k.
// O(n^2 log(k + 1)) time and O(1) auxiliary space; inputs are read-only.
function solve(nums, k) {
  function gcd(left, right) {
    while (right !== 0) [left, right] = [right, left % right];
    return left;
  }
  let answer = 0;
  for (let left = 0; left < nums.length; left += 1) {
    let current = 1;
    for (let right = left; right < nums.length; right += 1) {
      const value = nums[right];
      if (k % value !== 0) break;
      current = current / gcd(current, value) * value;
      if (current > k || k % current !== 0) break;
      if (current === k) answer += 1;
    }
  }
  return answer;
}

const subarrayLCM = solve;
class Solution {
  subarrayLCM(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, subarrayLCM };
