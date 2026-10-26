'use strict';

// 3072. Distribute Elements Into Two Arrays II.
// Two Fenwick trees count strictly larger prior values; O(n log n) time and O(n) space. Inputs are preserved and the result is fresh.

function solve(nums) {
  const values = [...new Set(nums)].sort((a, b) => a - b), ranks = new Map(values.map((value, index) => [value, index + 1]));
  const trees = [Array(values.length + 1).fill(0), Array(values.length + 1).fill(0)], arrays = [[], []];
  function prefix(tree, index) { let sum = 0; for (; index > 0; index -= index & -index) sum += tree[index]; return sum; }
  nums.forEach((value, position) => {
    const rank = ranks.get(value);
    let chosen = position;
    if (position >= 2) {
      const first = arrays[0].length - prefix(trees[0], rank), second = arrays[1].length - prefix(trees[1], rank);
      chosen = first > second || (first === second && arrays[0].length <= arrays[1].length) ? 0 : 1;
    }
    arrays[chosen].push(value);
    for (let index = rank; index < trees[chosen].length; index += index & -index) trees[chosen][index] += 1;
  });
  return arrays[0].concat(arrays[1]);
}

const resultArray = solve;
class Solution {
  resultArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, resultArray };
