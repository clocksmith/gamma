'use strict';

// 3233. Find the Count of Numbers Which Are Not Special (Medium).
// Specification: https://leetcode.com/problems/find-the-count-of-numbers-which-are-not-special/description/
function solve(l, r) {
  let limit = Math.floor(Math.sqrt(r));
  while ((limit + 1) * (limit + 1) <= r) limit++;
  while (limit * limit > r) limit--;
  const isPrime = new Array(limit + 1).fill(true);
  if (limit >= 0) isPrime[0] = false;
  if (limit >= 1) isPrime[1] = false;
  for (let i = 2; i * i <= limit; i++) if (isPrime[i])
    for (let j = i * i; j <= limit; j += i) isPrime[j] = false;
  let cnt = 0;
  for (let p = 2; p <= limit; p++)
    if (isPrime[p] && p * p >= l && p * p <= r) cnt++;
  return (r - l + 1) - cnt;
}
const nonSpecialCount = solve;
class Solution { nonSpecialCount(l, r) { return solve(l, r); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nonSpecialCount };
