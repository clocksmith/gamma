'use strict';

// 3621. Number of Integers With Popcount-Depth Equal to K I.
// Count bounded bit strings by population count and classify exact reduction depth, treating one separately; O(log^2 n) arithmetic operations and space. Inputs are preserved.

function solve(n, k) {
  if (n < 1) return 0;
  if (k === 0) return 1;
  const digits = BigInt(n).toString(2), length = digits.length, choose = [[1n]];
  for (let row = 1; row <= length; row += 1) {
    const current = Array(row + 1).fill(1n), previous = choose[row - 1];
    for (let index = 1; index < row; index += 1) current[index] = previous[index - 1] + previous[index];
    choose.push(current);
  }
  const counts = Array(length + 1).fill(0n), depth = new Int32Array(length + 1);
  let ones = 0;
  for (let index = 0; index < length; index += 1) {
    if (digits[index] !== '1') continue;
    const remaining = length - index - 1;
    for (let extra = 0; extra <= remaining; extra += 1) counts[ones + extra] += choose[remaining][extra];
    ones += 1;
  }
  counts[ones] += 1n;
  let answer = 0n;
  for (let value = 1; value <= length; value += 1) {
    if (value > 1) {
      let bits = value, amount = 0;
      while (bits) { bits &= bits - 1; amount += 1; }
      depth[value] = 1 + depth[amount];
    }
    if (1 + depth[value] === k) answer += counts[value];
  }
  if (k === 1) answer -= 1n;
  return Number(answer);
}

const popcountDepth = solve;
class Solution {
  popcountDepth(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, popcountDepth };
