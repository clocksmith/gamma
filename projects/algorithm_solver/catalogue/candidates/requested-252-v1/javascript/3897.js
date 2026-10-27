/**
 * 3897. Maximum Value of Concatenated Binary Segments
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-value-of-concatenated-binary-segments/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3897.Maximum%20Value%20of%20Concatenated%20Binary%20Segments/README_EN.md
 * Complexity: O(n log n + total bits) time; O(n) space.
 * Total bit count <= 2e5. Arithmetic never exceeds 2*modulus; input arrays preserved.
 */

function solve(nums1, nums0) {
  const segments = nums1.map((ones, index) => [ones, nums0[index]]);
  const group = segment => segment[1] === 0 ? 0 : segment[0] > 0 ? 1 : 2;
  segments.sort((a, b) => group(a) - group(b) || b[0] - a[0] || a[1] - b[1]);
  const modulus = 1000000007;
  let answer = 0;
  for (const [ones, zeros] of segments) {
    for (let count = 0; count < ones; count += 1) answer = (2 * answer + 1) % modulus;
    for (let count = 0; count < zeros; count += 1) answer = (2 * answer) % modulus;
  }
  return answer;
}

function maxValue(nums1, nums0) {
  return solve(nums1, nums0);
}

class Solution {
  maxValue(nums1, nums0) {
    return solve(nums1, nums0);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxValue, Solution };
}
