'use strict';

// 1982. Find Array Given Subset Sums: signed multiset partition using the smallest adjacent difference.
// O(n * 2^n) time and O(2^n) auxiliary space. Inputs are preserved.
function solve(n, sums) {
  let remaining = sums.slice().sort((a, b) => a - b);
  const answer = [];
  for (let round = 0; round < n; round += 1) {
    const difference = remaining[1] - remaining[0];
    const counts = new Map();
    for (const value of remaining) counts.set(value, (counts.get(value) || 0) + 1);
    const lower = [];
    const upper = [];
    for (const value of remaining) {
      if (counts.get(value) === 0) continue;
      counts.set(value, counts.get(value) - 1);
      counts.set(value + difference, counts.get(value + difference) - 1);
      lower.push(value);
      upper.push(value + difference);
    }
    if (lower.includes(0)) {
      answer.push(difference);
      remaining = lower;
    } else {
      answer.push(-difference);
      remaining = upper;
    }
  }
  return answer;
}

const recoverArray = solve;
class Solution {
  recoverArray(n, sums) { return solve(n, sums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, recoverArray };
