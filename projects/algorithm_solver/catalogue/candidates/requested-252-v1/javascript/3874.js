/**
 * 3874. Valid Subarrays With Exactly One Peak
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(nums, k).
 * Algorithm: Count legal left/right endpoint choices around each original-array peak, excluding neighboring peaks.
 * Complexity: O(n) time; O(n) space.
 * Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
 * Mutation: Does not mutate input arrays, rows, strings, or trees.
 * Interface: Ordered-positional solve; native forwarding name included only when confirmed.
 * Specification: https://leetcode.com/problems/valid-subarrays-with-exactly-one-peak/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3874.Valid%20Subarrays%20With%20Exactly%20One%20Peak/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: Peak status is determined in nums, not recomputed within a subarray. A singleton containing a peak is valid.
 */

function solve(nums, k) {
  const peaks = [];
  for (let index = 1; index + 1 < nums.length; index += 1) {
    if (nums[index] > nums[index - 1] && nums[index] > nums[index + 1]) peaks.push(index);
  }
  let total = 0;
  for (let offset = 0; offset < peaks.length; offset += 1) {
    const peak = peaks[offset];
    const previous = offset === 0 ? -1 : peaks[offset - 1];
    const following = offset + 1 === peaks.length ? nums.length : peaks[offset + 1];
    const left = Math.max(0, peak - k, previous + 1);
    const right = Math.min(nums.length - 1, peak + k, following - 1);
    total += (peak - left + 1) * (right - peak + 1);
  }
  return total;
}

function validSubarrays(nums, k) {
  return solve(nums, k);
}

class Solution {
  validSubarrays(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve, validSubarrays, Solution };
}
