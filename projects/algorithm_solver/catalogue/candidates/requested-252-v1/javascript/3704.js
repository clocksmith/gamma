/**
 * 3704. Count No-Zero Pairs That Sum to N
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-no-zero-pairs-that-sum-to-n/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3704.Count%20No-Zero%20Pairs%20That%20Sum%20to%20N/README_EN.md
 * Complexity: O(log n) states with a constant 100 digit-pair factor; O(log n) digit storage.
 * Ordered positive pairs. JavaScript BigInt counts internally; answer <= n-1 <= 1e15 converts exactly to Number.
 */

function solve(n) {
  const digits = String(n).split('').reverse().map(Number).concat(0);
  let states = Array(8).fill(0n); states[0] = 1n;
  for (let position = 0; position < digits.length; position += 1) {
    const next = Array(8).fill(0n);
    for (let state = 0; state < 8; state += 1) {
      if (states[state] === 0n) continue;
      const carry = Math.floor(state / 4), endedA = (state & 2) !== 0, endedB = (state & 1) !== 0;
      const lowA = endedA ? 0 : (position === 0 ? 1 : 0), highA = endedA ? 0 : 9;
      const lowB = endedB ? 0 : (position === 0 ? 1 : 0), highB = endedB ? 0 : 9;
      for (let a = lowA; a <= highA; a += 1) {
        for (let b = lowB; b <= highB; b += 1) {
          const total = carry + a + b;
          if (total % 10 !== digits[position]) continue;
          const nextState = Math.floor(total / 10) * 4 + (endedA || a === 0 ? 2 : 0) + (endedB || b === 0 ? 1 : 0);
          next[nextState] += states[state];
        }
      }
    }
    states = next;
  }
  return Number(states[3]);
}

function countNoZeroPairs(n) {
  return solve(n);
}

class Solution {
  countNoZeroPairs(n) {
    return solve(n);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countNoZeroPairs, Solution };
}
