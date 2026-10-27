/**
 * 4072. Maximum Alternating Subarray Sum With One Deletion
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-alternating-subarray-sum-with-one-deletion/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4072.Maximum%20Alternating%20Subarray%20Sum%20With%20One%20Deletion/README_EN.md
 * Complexity: O(n) time, O(1) space.
 * States track parity of retained subarray length, not original index. Deleting the current element preserves retained parity; keeping it flips parity. Empty subarrays are never admitted. Inputs preserved.
 */

function solve(nums) {
  let odd=-Infinity,even=-Infinity,deletedOdd=-Infinity,deletedEven=-Infinity,answer=-Infinity;
  for(const value of nums) {
    const nextOdd=Math.max(value,even+value),nextEven=odd-value;
    const nextDeletedOdd=Math.max(deletedEven+value,odd),nextDeletedEven=Math.max(deletedOdd-value,even);
    odd=nextOdd;even=nextEven;deletedOdd=nextDeletedOdd;deletedEven=nextDeletedEven;
    answer=Math.max(answer,odd,even,deletedOdd,deletedEven);
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
