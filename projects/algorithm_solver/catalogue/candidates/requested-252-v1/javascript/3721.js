/**
 * 3721. Longest Balanced Subarray II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/longest-balanced-subarray-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3721.Longest%20Balanced%20Subarray%20II/README_EN.md
 * Complexity: O(n log n) time; O(n) space.
 * Inputs preserved. Balance across adjacent candidate starts changes by at most one; min/max pruning locates an actual zero.
 */

function solve(nums) {
  const n = nums.length;
  const minimum = Array(4 * n).fill(0), maximum = Array(4 * n).fill(0), lazy = Array(4 * n).fill(0);
  function apply(node, change) { minimum[node] += change; maximum[node] += change; lazy[node] += change; }
  function push(node) {
    if (lazy[node] !== 0) { apply(node * 2, lazy[node]); apply(node * 2 + 1, lazy[node]); lazy[node] = 0; }
  }
  function update(node, left, right, begin, end, change) {
    if (begin <= left && right <= end) { apply(node, change); return; }
    push(node);
    const middle = Math.floor((left + right) / 2);
    if (begin <= middle) update(node * 2, left, middle, begin, end, change);
    if (end > middle) update(node * 2 + 1, middle + 1, right, begin, end, change);
    minimum[node] = Math.min(minimum[node * 2], minimum[node * 2 + 1]);
    maximum[node] = Math.max(maximum[node * 2], maximum[node * 2 + 1]);
  }
  function earliestZero(node, left, right, end) {
    if (left > end || minimum[node] > 0 || maximum[node] < 0) return -1;
    if (left === right) return left;
    push(node);
    const middle = Math.floor((left + right) / 2);
    const found = earliestZero(node * 2, left, middle, end);
    return found !== -1 ? found : earliestZero(node * 2 + 1, middle + 1, right, end);
  }
  const last = new Map();
  let answer = 0;
  for (let right = 0; right < n; right += 1) {
    const value = nums[right], previous = last.has(value) ? last.get(value) : -1;
    update(1, 0, n - 1, previous + 1, right, value % 2 === 0 ? 1 : -1);
    last.set(value, right);
    const left = earliestZero(1, 0, n - 1, right);
    if (left !== -1) answer = Math.max(answer, right - left + 1);
  }
  return answer;
}

function longestBalanced(nums) {
  return solve(nums);
}

class Solution {
  longestBalanced(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, longestBalanced, Solution };
}
