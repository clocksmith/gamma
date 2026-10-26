'use strict';

// 2802. Find The K-th Lucky Number: map the successor binary digits to four and seven.
// O(log(k + 1)) time and output space; inputs are read-only.
function solve(k) {
  const bits = (k + 1).toString(2).slice(1);
  return [...bits].map(bit => bit === '0' ? '4' : '7').join('');
}

const kthLuckyNumber = solve;
class Solution {
  kthLuckyNumber(k) { return solve(k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthLuckyNumber };
