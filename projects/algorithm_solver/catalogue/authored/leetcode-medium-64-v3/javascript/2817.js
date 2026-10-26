'use strict';

// 2817. Minimum Absolute Difference Between Elements With Constraint: query predecessor and successor among sufficiently old values with a Fenwick tree.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, x) {
  if (x === 0) return 0;
  const values = [...new Set(nums)].sort((left, right) => left - right);
  const ranks = new Map(values.map((value, index) => [value, index + 1]));
  const tree = new Int32Array(values.length + 1);
  function insert(index) {
    while (index < tree.length) {
      tree[index] += 1;
      index += index & -index;
    }
  }
  function prefixCount(index) {
    let total = 0;
    while (index > 0) {
      total += tree[index];
      index -= index & -index;
    }
    return total;
  }
  let highestStep = 1;
  while (highestStep * 2 <= values.length) highestStep *= 2;
  function select(order) {
    let index = 0;
    for (let step = highestStep; step > 0; step = Math.floor(step / 2)) {
      const following = index + step;
      if (following < tree.length && tree[following] < order) {
        order -= tree[following];
        index = following;
      }
    }
    return values[index];
  }
  let best = Infinity;
  for (let index = x; index < nums.length; index += 1) {
    insert(ranks.get(nums[index - x]));
    const value = nums[index];
    const below = prefixCount(ranks.get(value) - 1);
    if (below > 0) best = Math.min(best, value - select(below));
    if (below < index - x + 1) best = Math.min(best, select(below + 1) - value);
  }
  return best;
}

const minAbsoluteDifference = solve;
class Solution {
  minAbsoluteDifference(nums, x) { return solve(nums, x); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minAbsoluteDifference };
