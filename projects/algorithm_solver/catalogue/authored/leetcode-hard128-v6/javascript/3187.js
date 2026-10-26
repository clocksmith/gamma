'use strict';

// 3187. Peaks in Array.
// Fenwick sums over peak indicators; each update affects at most three indicators. O((n+q) log n) time, O(n) space. Inputs are preserved.

function solve(nums, queries) {
  const values = nums.slice(), n = nums.length, tree = Array(n + 1).fill(0);
  function peak(i) { return i > 0 && i < n - 1 && values[i] > values[i - 1] && values[i] > values[i + 1]; }
  function add(index, change) { for (let i = index + 1; i <= n; i += i & -i) tree[i] += change; }
  function prefix(end) { let sum = 0; for (; end > 0; end -= end & -end) sum += tree[end]; return sum; }
  for (let i = 1; i < n - 1; i += 1) if (peak(i)) add(i, 1);
  const answer = [];
  for (const [kind, first, second] of queries) {
    if (kind === 1) answer.push(second - first > 1 ? prefix(second) - prefix(first + 1) : 0);
    else {
      const affected = [];
      for (let i = Math.max(1, first - 1); i <= Math.min(n - 2, first + 1); i += 1) affected.push([i, Number(peak(i))]);
      values[first] = second;
      for (const [i, old] of affected) add(i, Number(peak(i)) - old);
    }
  }
  return answer;
}

const countOfPeaks = solve;
class Solution {
  countOfPeaks(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOfPeaks };
