/**
 * 3991. Sort Array Using Prefix Reversals
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/sort-array-using-prefix-reversals/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3991.Sort%20Array%20Using%20Prefix%20Reversals/README_EN.md
 * Complexity: O(n!*|pre|*n) time, O(n!*n) space; n<=8.
 * BFS over permutations, exact string encoding is unambiguous for digits 0..7. Inputs preserved.
 */

function solve(nums, pre) {
  const start = nums.join(''), target = Array.from({length: nums.length}, (_, i) => i).join('');
  if (start === target) return 0;
  const lengths = pre.filter(length => length > 1), seen = new Set([start]), queue = [[start, 0]];
  for (let head = 0; head < queue.length; head++) {
    const [state, distance] = queue[head];
    for (const length of lengths) {
      const following = state.slice(0, length).split('').reverse().join('') + state.slice(length);
      if (following === target) return distance + 1;
      if (!seen.has(following)) { seen.add(following); queue.push([following, distance + 1]); }
    }
  }
  return -1;
}

function sortArray(nums, pre) {
  return solve(nums, pre);
}

class Solution {
  sortArray(nums, pre) {
    return solve(nums, pre);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, sortArray, Solution };
}
