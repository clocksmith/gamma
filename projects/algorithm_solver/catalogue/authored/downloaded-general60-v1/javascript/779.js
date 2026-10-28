'use strict';

// 779. K-th Symbol in Grammar (Medium).
// Specification: https://leetcode.com/problems/k-th-symbol-in-grammar/description/
function solve(n, k) {
  let value = k - 1;
  let parity = 0;
  while (value > 0) { parity ^= value & 1; value >>= 1; }
  return parity;
}
const kthGrammar = solve;
class Solution { kthGrammar(n, k) { return solve(n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthGrammar };
