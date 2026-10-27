'use strict';

// 3994. Minimum Adjacent Swaps to Partition Array.
// Specification: https://leetcode.com/problems/minimum-adjacent-swaps-to-partition-array/description/
// O(n) time, O(1) auxiliary space. Inputs are preserved.
function solve(nums, a, b) {
  let middle = 0, high = 0, answer = 0;
  for (const value of nums) {
    if (value < a) answer = (answer + middle + high) % 1000000007;
    else if (value <= b) { answer = (answer + high) % 1000000007; middle++; }
    else high++;
  }
  return answer;
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
