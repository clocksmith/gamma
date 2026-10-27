'use strict';

// 440. K-th Smallest in Lexicographical Order.

function solve(n, k) {
  let current = 1;
  k -= 1;
  while (k > 0) {
    let first = current, following = current + 1, count = 0;
    while (first <= n) {
      count += Math.min(n + 1, following) - first;
      first *= 10; following *= 10;
    }
    if (count <= k) { current += 1; k -= count; }
    else { current *= 10; k -= 1; }
  }
  return current;
}

const findKthNumber = solve;
class Solution {
  findKthNumber(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findKthNumber };
