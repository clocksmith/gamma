/**
 * 3985. Palindromic Subarray Sum
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/palindromic-subarray-sum/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3985.Palindromic%20Subarray%20Sum/README_EN.md
 * Complexity: O(n) time, O(n) space.
 * Manacher radii use exact element comparisons, not hashes. Strictly positive elements make the largest radius optimal at each center; sums <=1e14. Native method unconfirmed.
 */

function solve(nums) {
  const n = nums.length, prefix = new Float64Array(n + 1);
  for (let i = 0; i < n; i++) prefix[i + 1] = prefix[i] + nums[i];
  let answer = nums[0], left = 0, right = -1;
  const odd = new Int32Array(n), even = new Int32Array(n);
  for (let i = 0; i < n; i++) {
    let radius = i > right ? 1 : Math.min(odd[left + right - i], right - i + 1);
    while (i - radius >= 0 && i + radius < n && nums[i - radius] === nums[i + radius]) radius++;
    odd[i] = radius;
    answer = Math.max(answer, prefix[i + radius] - prefix[i - radius + 1]);
    if (i + radius - 1 > right) { left = i - radius + 1; right = i + radius - 1; }
  }
  left = 0; right = -1;
  for (let i = 0; i < n; i++) {
    let radius = i > right ? 0 : Math.min(even[left + right - i + 1], right - i + 1);
    while (i - radius - 1 >= 0 && i + radius < n && nums[i - radius - 1] === nums[i + radius]) radius++;
    even[i] = radius;
    if (radius) answer = Math.max(answer, prefix[i + radius] - prefix[i - radius]);
    if (i + radius - 1 > right) { left = i - radius; right = i + radius - 1; }
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
