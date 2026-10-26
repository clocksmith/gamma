'use strict';

// 2968. Apply Operations to Maximize Frequency Score.
// Sorted sliding windows with exact median conversion costs; O(n log n) time, O(n) space. Inputs are preserved.

function solve(nums, k) {
  const values = nums.slice().sort((a, b) => a - b), prefix = [0];
  for (const value of values) prefix.push(prefix[prefix.length - 1] + value);
  function cost(left, right) {
    const middle = Math.floor((left + right) / 2);
    return values[middle] * (middle - left) - prefix[middle] + prefix[left] + prefix[right + 1] - prefix[middle + 1] - values[middle] * (right - middle);
  }
  let left = 0, answer = 0;
  for (let right = 0; right < values.length; right += 1) {
    while (cost(left, right) > k) left += 1;
    answer = Math.max(answer, right - left + 1);
  }
  return answer;
}

const maxFrequencyScore = solve;
class Solution {
  maxFrequencyScore(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxFrequencyScore };
