'use strict';

// 3444. Minimum Increments for Target Multiples in an Array.
// Subset-LCM coverage dynamic programming with a feasible distinct-element upper bound; O(n*4^m+m*2^m log V) time and O(2^m) space, m<=4. Inputs are preserved.

function solve(nums, target) {
  const size = 1 << target.length, upper = target.reduce((sum, value) => sum + value - 1, 0);
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const cap = maximum + upper, multiples = Array(size).fill(1);
  function gcd(a, b) { while (b) { const remainder = a % b; a = b; b = remainder; } return a; }
  for (let mask = 1; mask < size; mask += 1) {
    const bit = mask & -mask, previous = multiples[mask ^ bit], value = target[31 - Math.clz32(bit)];
    multiples[mask] = previous > cap ? cap + 1 : Math.min(cap + 1, previous / gcd(previous, value) * value);
  }
  let best = Array(size).fill(Infinity);
  best[0] = 0;
  for (const value of nums) {
    const following = best.slice();
    for (let covered = 0; covered < size; covered += 1) {
      if (best[covered] > upper) continue;
      for (let mask = 1; mask < size; mask += 1) {
        const multiple = multiples[mask];
        if (multiple > cap) continue;
        const extra = (multiple - value % multiple) % multiple, combined = covered | mask;
        following[combined] = Math.min(following[combined], best[covered] + extra);
      }
    }
    best = following;
    if (best[size - 1] === 0) return 0;
  }
  return best[size - 1];
}

const minimumIncrements = solve;
class Solution {
  minimumIncrements(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumIncrements };
