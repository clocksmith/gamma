/**
 * 3895. Count Digit Appearances
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-digit-appearances/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3895.Count%20Digit%20Appearances/README_EN.md
 * Complexity: O(total decimal digits) time; O(log max(nums)) temporary space.
 * Positive integers <= 1e6; input preserved.
 */

function solve(nums, digit) {
  const target = String(digit);
  let answer = 0;
  for (const value of nums) {
    for (const character of String(value)) if (character === target) answer += 1;
  }
  return answer;
}

function countDigitOccurrences(nums, digit) {
  return solve(nums, digit);
}

class Solution {
  countDigitOccurrences(nums, digit) {
    return solve(nums, digit);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countDigitOccurrences, Solution };
}
