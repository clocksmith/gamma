/**
 * 3934. Smallest Unique Subarray
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/smallest-unique-subarray/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3934.Smallest%20Unique%20Subarray/README_EN.md
 * Complexity: O(n log^2 n) comparison-sort time, O(n) space.
 * Exact suffix ranks and Kasai LCP, no probabilistic hash. Inputs preserved; performance not measured.
 */

function solve(nums) {
  const n = nums.length;
  const values = [...new Set(nums)].sort((a, b) => a - b);
  const ids = new Map(values.map((value, index) => [value, index]));
  let rank = nums.map(value => ids.get(value));
  const suffixes = Array.from({ length: n }, (_, index) => index);
  for (let width = 1; width < n; width *= 2) {
    const second = index => index + width < n ? rank[index + width] : -1;
    suffixes.sort((a, b) => rank[a] - rank[b] || second(a) - second(b));
    const nextRank = Array(n).fill(0);
    for (let index = 1; index < n; index += 1) {
      const previous = suffixes[index - 1];
      const current = suffixes[index];
      nextRank[current] = nextRank[previous] + (rank[previous] !== rank[current] || second(previous) !== second(current) ? 1 : 0);
    }
    rank = nextRank;
    if (rank[suffixes[n - 1]] === n - 1) break;
  }
  const position = new Int32Array(n);
  suffixes.forEach((start, index) => { position[start] = index; });
  const lcp = new Int32Array(n);
  let common = 0;
  for (let start = 0; start < n; start += 1) {
    const index = position[start];
    if (index === 0) { common = 0; continue; }
    const previous = suffixes[index - 1];
    while (start + common < n && previous + common < n && nums[start + common] === nums[previous + common]) common += 1;
    lcp[index] = common;
    common = Math.max(0, common - 1);
  }
  let answer = n;
  for (let index = 0; index < n; index += 1) {
    const needed = 1 + Math.max(lcp[index], index + 1 < n ? lcp[index + 1] : 0);
    if (needed <= n - suffixes[index]) answer = Math.min(answer, needed);
  }
  return answer;
}

function smallestUniqueSubarray(nums) {
  return solve(nums);
}

class Solution {
  smallestUniqueSubarray(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, smallestUniqueSubarray, Solution };
}
