'use strict';

// 3850. Count Sequences to K.
// O(n S) time and O(S) space for S reachable exponent states; exact rational equality via prime exponents, counts <= 3^19.
function solve(nums, k) {
  const needed = [];
  let remaining = k;
  for (const prime of [2, 3, 5]) {
    let exponent = 0;
    while (remaining % prime === 0) {
      remaining /= prime;
      exponent += 1;
    }
    needed.push(exponent);
  }
  if (remaining !== 1 || needed[0] > 2 * nums.length || needed[1] > nums.length || needed[2] > nums.length) return 0;
  const base = 4 * nums.length + 1;
  const weights = [0, 0, base * base, base, 2 * base * base, 1, base * base + base];
  let states = new Map([[0, 1]]);
  for (const value of nums) {
    const delta = weights[value];
    const following = new Map();
    for (const [key, count] of states) {
      for (const nextKey of [key, key + delta, key - delta]) following.set(nextKey, (following.get(nextKey) || 0) + count);
    }
    states = following;
  }
  const target = needed[0] * base * base + needed[1] * base + needed[2];
  return states.get(target) || 0;
}

const countSequences = solve;
class Solution {
  countSequences(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSequences };
