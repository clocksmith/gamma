'use strict';

// 3835. Count Subarrays With Cost Less Than or Equal to K.
// O(n) time and O(n) space; monotone extrema queues and a shrinking valid window.
function solve(nums, k) {
  const minimum = [];
  const maximum = [];
  let minHead = 0;
  let maxHead = 0;
  let left = 0;
  let answer = 0;
  for (let right = 0; right < nums.length; right += 1) {
    const value = nums[right];
    while (minimum.length > minHead && nums[minimum[minimum.length - 1]] >= value) minimum.pop();
    while (maximum.length > maxHead && nums[maximum[maximum.length - 1]] <= value) maximum.pop();
    minimum.push(right);
    maximum.push(right);
    while ((nums[maximum[maxHead]] - nums[minimum[minHead]]) * (right - left + 1) > k) {
      if (minimum[minHead] === left) minHead += 1;
      if (maximum[maxHead] === left) maxHead += 1;
      left += 1;
    }
    answer += right - left + 1;
  }
  return answer;
}

const countSubarrays = solve;
class Solution {
  countSubarrays(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubarrays };
