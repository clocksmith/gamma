'use strict';

// 3752. Lexicographically Smallest Negated Permutation that Sums to Target.
// O(n) time and O(n) space; greedily include the largest feasible negative magnitude.
function solve(n, target) {
  const total = n * (n + 1) / 2;
  if (Math.abs(target) > total || (total - target) % 2 !== 0) return [];
  let remaining = (total - target) / 2;
  const negative = new Uint8Array(n + 1);
  const answer = [];
  for (let value = n; value >= 1; value -= 1) {
    if (value <= remaining) {
      remaining -= value;
      negative[value] = 1;
      answer.push(-value);
    }
  }
  for (let value = 1; value <= n; value += 1) {
    if (!negative[value]) answer.push(value);
  }
  return answer;
}

const lexSmallestNegatedPerm = solve;
class Solution {
  lexSmallestNegatedPerm(n, target) { return solve(n, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lexSmallestNegatedPerm };
