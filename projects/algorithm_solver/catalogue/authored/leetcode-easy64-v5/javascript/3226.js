'use strict';

// 3226. Number of Bit Changes to Make Two Integers Equal (Easy).
// Specification: https://leetcode.com/problems/number-of-bit-changes-to-make-two-integers-equal/description/
// O(log(n + k)) time, O(1) space; bitwise operations are safe for n, k <= 1000000.
function solve(n, k) {
  if ((n & k) !== k) return -1;
  let remaining = n ^ k;
  let changes = 0;
  while (remaining > 0) {
    remaining &= remaining - 1;
    changes++;
  }
  return changes;
}

const minChanges = solve;
class Solution {
  minChanges(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minChanges };
