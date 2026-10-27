'use strict';

// 634. Find the Derangement of An Array. Use D(n)=(n-1)*(D(n-1)+D(n-2)); only two states are retained.

function solve(n) {
  const modulus = 1000000007;
  let previous = 1, current = 0;
  if (n === 0) return previous;
  for (let length = 2; length <= n; length += 1) [previous, current] = [current, (length - 1) * (current + previous) % modulus];
  return current;
}

const findDerangement = solve;
class Solution {
  findDerangement(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDerangement };
