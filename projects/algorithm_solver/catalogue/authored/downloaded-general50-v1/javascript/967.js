'use strict';

// 967. Numbers With Same Consecutive Differences (Medium).
// Specification: https://leetcode.com/problems/numbers-with-same-consecutive-differences/description/
function solve(n, k) {
  if (n === 1) return [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
  const result = [];
  function backtrack(current, remaining) {
    if (remaining === 0) { result.push(Number(current)); return; }
    const last = Number(current[current.length - 1]);
    const candidates = [...new Set([last + k, last - k])];
    for (const next of candidates) {
      if (next < 0 || next > 9) continue;
      backtrack(current + String(next), remaining - 1);
    }
  }
  for (let first = 1; first <= 9; first++) backtrack(String(first), n - 1);
  return result.sort((a, b) => a - b);
}
const numsSameConsecDiff = solve;
class Solution { numsSameConsecDiff(n, k) { return solve(n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numsSameConsecDiff };
