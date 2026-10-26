'use strict';

// 3725. Count Ways to Choose Coprime Integers from Rows.
// O(M^2 log M + rows * M * columns) time and O(M^2) space; M <= 150.
function solve(mat) {
  const modulus = 1000000007;
  let maximum = 1;
  for (const row of mat) for (const value of row) maximum = Math.max(maximum, value);
  function gcd(left, right) {
    while (right !== 0) [left, right] = [right, left % right];
    return left;
  }
  const gcds = Array.from({ length: maximum + 1 }, (_, left) =>
    Array.from({ length: maximum + 1 }, (_, right) => gcd(left, right)));
  let ways = new Float64Array(maximum + 1);
  ways[0] = 1;
  for (const row of mat) {
    const frequency = new Map();
    for (const value of row) frequency.set(value, (frequency.get(value) || 0) + 1);
    const following = new Float64Array(maximum + 1);
    for (let previous = 0; previous <= maximum; previous += 1) {
      const count = ways[previous];
      if (count === 0) continue;
      for (const [value, occurrences] of frequency) {
        const key = gcds[previous][value];
        following[key] = (following[key] + count * occurrences) % modulus;
      }
    }
    ways = following;
  }
  return ways[1];
}

const countCoprime = solve;
class Solution {
  countCoprime(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCoprime };
