'use strict';

// 3669. Balanced K-Factor Decomposition.
// O(sqrt(n) + k * D^(k-1)) worst-case time, O(D + k) space; D is the divisor count.
function solve(n, k) {
  const divisors = [];
  for (let factor = 1; factor * factor <= n; factor += 1) {
    if (n % factor === 0) {
      divisors.push(factor);
      if (factor * factor !== n) divisors.push(n / factor);
    }
  }
  divisors.sort((left, right) => left - right);
  let answer = Array(k - 1).fill(1).concat(n);
  let bestGap = n - 1;
  const path = [];
  function search(remaining, slots, lower) {
    if (slots === 1) {
      if (remaining >= lower) {
        const first = path.length > 0 ? path[0] : remaining;
        const gap = remaining - first;
        if (gap < bestGap) {
          bestGap = gap;
          answer = path.concat(remaining);
        }
      }
      return;
    }
    for (const factor of divisors) {
      if (factor < lower) continue;
      let power = 1;
      for (let count = 0; count < slots && power <= remaining; count += 1) power *= factor;
      if (power > remaining) break;
      if (remaining % factor === 0) {
        path.push(factor);
        search(remaining / factor, slots - 1, factor);
        path.pop();
      }
    }
  }
  search(n, k, 1);
  return answer;
}

const minDifference = solve;
class Solution {
  minDifference(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minDifference };
