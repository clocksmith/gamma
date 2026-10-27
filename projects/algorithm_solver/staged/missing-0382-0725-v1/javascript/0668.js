'use strict';

// 668. Kth Smallest Number in Multiplication Table.

function solve(m, n, k) {
  if (m > n) [m, n] = [n, m];
  let low = 1, high = m * n;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    let count = 0;
    for (let row = 1; row <= m; row += 1) count += Math.min(n, Math.floor(middle / row));
    if (count >= k) high = middle; else low = middle + 1;
  }
  return low;
}

const findKthNumber = solve;
class Solution {
  findKthNumber(m, n, k) { return solve(m, n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findKthNumber };
