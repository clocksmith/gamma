'use strict';

// 3470. Permutations IV.
// Unrank alternating-parity permutations using exact factorial completion counts; O(n^2) arithmetic operations and O(n) space. Inputs are preserved.

function solve(n, k) {
  const factorial = [1n], used = Array(n + 1).fill(false), answer = [];
  for (let value = 1; value <= n; value += 1) factorial.push(factorial[value - 1] * BigInt(value));
  let rank = BigInt(k), odd = Math.ceil(n / 2), even = Math.floor(n / 2);
  for (let position = 0; position < n; position += 1) {
    let chosen = false;
    for (let value = 1; value <= n; value += 1) {
      if (used[value] || (answer.length && value % 2 === answer[answer.length - 1] % 2)) continue;
      const remainingOdd = odd - value % 2, remainingEven = even - (1 - value % 2);
      const remaining = n - position - 1, neededOdd = Math.floor((remaining + (value % 2 === 0 ? 1 : 0)) / 2);
      if (remainingOdd !== neededOdd || remainingEven !== remaining - neededOdd) continue;
      const completions = factorial[remainingOdd] * factorial[remainingEven];
      if (rank > completions) { rank -= completions; continue; }
      answer.push(value); used[value] = true; odd = remainingOdd; even = remainingEven; chosen = true; break;
    }
    if (!chosen) return [];
  }
  return answer;
}

const permute = solve;
class Solution {
  permute(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, permute };
