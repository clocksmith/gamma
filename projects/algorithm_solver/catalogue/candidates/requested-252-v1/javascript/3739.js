/**
 * 3739. Count Subarrays With Majority Element II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-subarrays-with-majority-element-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3739.Count%20Subarrays%20With%20Majority%20Element%20II/README_EN.md
 * Complexity: O(n log n) time; O(n) space.
 * Canonical solve(nums,target); native stub name pending. Counts up to n(n+1)/2 fit Number; inputs preserved.
 */

function solve(nums, target) {
  const n = nums.length, tree = Array(2 * n + 3).fill(0);
  function add(index) { while (index < tree.length) { tree[index] += 1; index += index & -index; } }
  function prefix(index) { let total = 0; while (index > 0) { total += tree[index]; index -= index & -index; } return total; }
  let balance = n + 1, answer = 0;
  add(balance);
  for (const value of nums) { balance += value === target ? 1 : -1; answer += prefix(balance - 1); add(balance); }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
