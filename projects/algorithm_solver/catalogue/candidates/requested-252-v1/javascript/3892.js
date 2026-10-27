/**
 * 3892. Minimum Operations to Achieve At Least K Peaks
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-achieve-at-least-k-peaks/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3892.Minimum%20Operations%20to%20Achieve%20At%20Least%20K%20Peaks/README_EN.md
 * Complexity: O(n*k) time; O(n+k) space.
 * Circular nonadjacent peak selection. 2 <= n <= 5000. Native judge method not established; canonical solve only.
 */

function solve(nums, k) {
  const n = nums.length;
  if (k === 0) return 0;
  if (k > Math.floor(n / 2)) return -1;
  const costs = nums.map((value, index) => Math.max(0, Math.max(nums[(index + n - 1) % n], nums[(index + 1) % n]) + 1 - value));
  function chain(left, right, needed) {
    if (needed === 0) return 0;
    if (needed > Math.floor((Math.max(0, right - left + 1) + 1) / 2)) return Infinity;
    let skip = Array(needed + 1).fill(Infinity);
    let take = Array(needed + 1).fill(Infinity);
    skip[0] = 0;
    for (let index = left; index <= right; index += 1) {
      const nextSkip = skip.map((value, count) => Math.min(value, take[count]));
      const nextTake = Array(needed + 1).fill(Infinity);
      for (let count = 1; count <= needed; count += 1) nextTake[count] = skip[count - 1] + costs[index];
      skip = nextSkip;
      take = nextTake;
    }
    return Math.min(skip[needed], take[needed]);
  }
  return Math.min(chain(1, n - 1, k), costs[0] + chain(2, n - 2, k - 1));
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
