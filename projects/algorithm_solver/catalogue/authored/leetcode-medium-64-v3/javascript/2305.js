'use strict';

// 2305. Fair Distribution of Cookies: partition subset sums with a minimax dynamic program.
// O(k * 3^n) time and O(2^n) auxiliary space for n <= 8 bags; inputs are read-only.
function solve(cookies, k) {
  const size = 1 << cookies.length;
  const sums = new Array(size).fill(0);
  for (let mask = 1; mask < size; mask += 1) {
    const bit = mask & -mask;
    sums[mask] = sums[mask ^ bit] + cookies[31 - Math.clz32(bit)];
  }
  let best = new Array(size).fill(Infinity);
  best[0] = 0;
  for (let child = 0; child < k; child += 1) {
    const following = [...best];
    for (let mask = 1; mask < size; mask += 1) {
      for (let subset = mask; subset !== 0; subset = (subset - 1) & mask) {
        following[mask] = Math.min(following[mask], Math.max(best[mask ^ subset], sums[subset]));
      }
    }
    best = following;
  }
  return best[size - 1];
}

const distributeCookies = solve;
class Solution {
  distributeCookies(cookies, k) { return solve(cookies, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distributeCookies };
