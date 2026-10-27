// Original candidate. Contract: https://leetcode.com/problems/minimum-cost-to-make-array-equalindromic/
"use strict";

function solve(nums) {
  const values = nums.slice().sort((x, y) => x - y);
  const median = values[values.length >> 1];
  const digits = String(median);
  const length = digits.length;
  const prefix = Number(digits.slice(0, Math.ceil(length / 2)));
  const candidates = new Set([10 ** (length - 1) - 1, 10 ** length + 1]);

  // The closest feasible palindromes around a median minimize L1 cost.
  for (let head = Math.max(0, prefix - 1); head <= prefix + 1; head++) {
    const text = String(head);
    const mirrored = (length % 2 ? text.slice(0, -1) : text)
      .split('').reverse().join('');
    candidates.add(Number(text + mirrored));
  }

  let answer = Infinity;
  for (const palindrome of candidates) {
    if (palindrome <= 0 || palindrome >= 1e9) continue;
    let cost = 0;
    for (const value of values) cost += Math.abs(value - palindrome);
    answer = Math.min(answer, cost);
  }
  return answer;
}

module.exports = solve;
