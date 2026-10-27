'use strict';

// 481. Magical String.

function solve(n) {
  if (n <= 0) return 0;
  const sequence = [1, 2, 2];
  let head = 2, nextValue = 1;
  while (sequence.length < n) {
    const count = sequence[head++];
    for (let i = 0; i < count; i += 1) sequence.push(nextValue);
    nextValue = 3 - nextValue;
  }
  let ones = 0;
  for (let i = 0; i < n; i += 1) if (sequence[i] === 1) ones += 1;
  return ones;
}

const magicalString = solve;
class Solution {
  magicalString(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, magicalString };
