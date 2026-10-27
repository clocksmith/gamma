/**
 * 3942. Minimum Operations to Sort a Permutation
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-sort-a-permutation/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3942.Minimum%20Operations%20to%20Sort%20a%20Permutation/README_EN.md
 * Complexity: O(n) time, O(1) auxiliary space.
 * Only whole reversal and one-step LEFT rotation. Permutation 0..n-1, input preserved.
 */

function solve(nums) {
  const n = nums.length;
  const zero = nums.indexOf(0);
  let increasing = true;
  let decreasing = true;
  for (let offset = 0; offset < n; offset += 1) {
    if (nums[(zero + offset) % n] !== offset) increasing = false;
    if (nums[(zero - offset + n) % n] !== offset) decreasing = false;
  }
  let answer = Infinity;
  if (increasing) answer = Math.min(zero, n - zero + 2);
  if (decreasing) answer = Math.min(answer, zero + 2, n - zero);
  return answer === Infinity ? -1 : answer;
}

function minOperations(nums) {
  return solve(nums);
}

class Solution {
  minOperations(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minOperations, Solution };
}
