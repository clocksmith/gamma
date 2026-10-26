'use strict';

// 1649. Create Sorted Array through Instructions.
// Coordinate compression and Fenwick counts of smaller and larger entries; O(n log n) time, O(n) space. Inputs are preserved.

function solve(instructions) {
  const values = [...new Set(instructions)].sort((a, b) => a - b);
  const rank = new Map(values.map((value, index) => [value, index + 1]));
  const tree = Array(values.length + 1).fill(0);
  function prefix(index) {
    let result = 0;
    for (; index > 0; index -= index & -index) result += tree[index];
    return result;
  }
  let answer = 0;
  for (let inserted = 0; inserted < instructions.length; inserted += 1) {
    const index = rank.get(instructions[inserted]);
    answer = (answer + Math.min(prefix(index - 1), inserted - prefix(index))) % 1000000007;
    for (let i = index; i < tree.length; i += i & -i) tree[i] += 1;
  }
  return answer;
}

const createSortedArray = solve;
class Solution {
  createSortedArray(instructions) { return solve(instructions); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, createSortedArray };
