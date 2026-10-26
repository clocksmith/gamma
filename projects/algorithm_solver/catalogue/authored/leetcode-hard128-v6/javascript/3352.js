'use strict';

// 3352. Count K-Reducible Numbers Less Than N.
// Count smaller binary strings by population count, then classify reduction depth; O(L^2) time and space. Inputs are preserved.

function solve(s, k) {
  const modulus = 1000000007, length = s.length;
  if (k === 0) return length > 1 ? 1 : 0;
  const choose = [[1]];
  for (let row = 1; row <= length; row += 1) {
    const current = Array(row + 1).fill(1), previous = choose[row - 1];
    for (let index = 1; index < row; index += 1) current[index] = (previous[index - 1] + previous[index]) % modulus;
    choose.push(current);
  }
  const counts = Array(length + 1).fill(0), depth = new Int32Array(length + 1);
  let ones = 0;
  for (let index = 0; index < length; index += 1) {
    if (s[index] !== '1') continue;
    const remaining = length - index - 1;
    for (let extra = 0; extra <= remaining; extra += 1) counts[ones + extra] = (counts[ones + extra] + choose[remaining][extra]) % modulus;
    ones += 1;
  }
  let answer = 0;
  for (let value = 1; value <= length; value += 1) {
    if (value > 1) {
      let remaining = value, bits = 0;
      while (remaining !== 0) { remaining &= remaining - 1; bits += 1; }
      depth[value] = 1 + depth[bits];
    }
    if (1 + depth[value] <= k) answer = (answer + counts[value]) % modulus;
  }
  return answer;
}

const countKReducibleNumbers = solve;
class Solution {
  countKReducibleNumbers(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countKReducibleNumbers };
