'use strict';

// 3982. Sum of Integers with Maximum Digit Range.
// Specification: https://leetcode.com/problems/sum-of-integers-with-maximum-digit-range/description/
// O(n log M) time and O(1) auxiliary space. Inputs are preserved.
function solve(nums) {
  let bestRange = -1, answer = 0;
  for (const value of nums) {
    let remaining = value, minimum = 9, maximum = 0;
    do {
      const digit = remaining % 10;
      minimum = Math.min(minimum, digit); maximum = Math.max(maximum, digit);
      remaining = Math.floor(remaining / 10);
    } while (remaining);
    const range = maximum - minimum;
    if (range > bestRange) { bestRange = range; answer = 0; }
    if (range === bestRange) answer += value;
  }
  return answer;
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
