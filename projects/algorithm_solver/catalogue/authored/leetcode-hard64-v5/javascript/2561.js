'use strict';

// 2561. Rearranging Fruits. Pair opposite surplus values and allow swaps through the global minimum; O(n log n) time and O(n) space. Inputs are preserved.

function solve(basket1, basket2) {
  const difference = new Map();
  let smallest = Infinity;
  for (const value of basket1) {
    difference.set(value, (difference.get(value) || 0) + 1);
    smallest = Math.min(smallest, value);
  }
  for (const value of basket2) {
    difference.set(value, (difference.get(value) || 0) - 1);
    smallest = Math.min(smallest, value);
  }
  const surplus = [];
  for (const [value, count] of difference) {
    if (count % 2 !== 0) return -1;
    for (let copies = Math.abs(count) / 2; copies > 0; copies -= 1) surplus.push(value);
  }
  surplus.sort((a, b) => a - b);
  let answer = 0;
  for (let index = 0; index < surplus.length / 2; index += 1) answer += Math.min(surplus[index], 2 * smallest);
  return answer;
}

const minCost = solve;
class Solution {
  minCost(basket1, basket2) { return solve(basket1, basket2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
