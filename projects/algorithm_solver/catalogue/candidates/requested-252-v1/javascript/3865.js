/**
 * 3865. Reverse K Subarrays
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(nums, k).
 * Algorithm: Two-pointer reversal inside each of k equal-length contiguous pieces.
 * Complexity: O(n) time; O(1) auxiliary space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Mutates nums in place and returns the same list/array object.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/reverse-k-subarrays/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3865.Reverse%20K%20Subarrays/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: k is the number of subarrays, not the length of each subarray.
 */

function solve(nums, k) {
  const width = nums.length / k;
  for (let start = 0; start < nums.length; start += width) {
    let left = start;
    let right = start + width - 1;
    while (left < right) {
      const saved = nums[left];
      nums[left] = nums[right];
      nums[right] = saved;
      left += 1;
      right -= 1;
    }
  }
  return nums;
}

function reverseSubarrays(nums, k) {
  return solve(nums, k);
}

class Solution {
  reverseSubarrays(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, reverseSubarrays, Solution };
}
