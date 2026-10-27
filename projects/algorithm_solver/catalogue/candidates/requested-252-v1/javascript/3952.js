/**
 * 3952. Maximum Total Value of Covered Indices
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-total-value-of-covered-indices/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3952.Maximum%20Total%20Value%20of%20Covered%20Indices/README_EN.md
 * Complexity: O(n) time, O(n) Python temporary space and O(1) JavaScript auxiliary space.
 * A run of r tokens can cover any r positions of its r+1-position left extension; positive values favor distinct coverage. Each token moves at most once. Inputs preserved; native method pending.
 */

function solve(nums, s) {
  let total = 0;
  let index = 0;
  while (index < nums.length) {
    if (s[index] === '0') { index++; continue; }
    const start = index;
    let sum = start > 0 ? nums[start - 1] : 0;
    let smallest = start > 0 ? nums[start - 1] : Infinity;
    while (index < nums.length && s[index] === '1') {
      sum += nums[index];
      smallest = Math.min(smallest, nums[index]);
      index++;
    }
    total += start === 0 ? sum : sum - smallest;
  }
  return total;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
