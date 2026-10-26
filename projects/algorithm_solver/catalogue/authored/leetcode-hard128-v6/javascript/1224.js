'use strict';

// 1224. Maximum Equal Frequency.
// Track frequencies and the number of values at each frequency; O(n) time and O(n) space. Inputs are preserved.

function solve(nums) {
  const counts = new Map();
  const frequencies = new Map();
  let largest = 0;
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    const old = counts.get(nums[index]) || 0;
    if (old > 0) frequencies.set(old, frequencies.get(old) - 1);
    counts.set(nums[index], old + 1);
    frequencies.set(old + 1, (frequencies.get(old + 1) || 0) + 1);
    largest = Math.max(largest, old + 1);
    const length = index + 1;
    if (largest === 1 ||
        (largest * (frequencies.get(largest) || 0) + 1 === length && frequencies.get(1) === 1) ||
        ((largest - 1) * ((frequencies.get(largest - 1) || 0) + 1) + 1 === length && frequencies.get(largest) === 1)) answer = length;
  }
  return answer;
}

const maxEqualFreq = solve;
class Solution {
  maxEqualFreq(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxEqualFreq };
