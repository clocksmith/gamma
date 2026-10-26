'use strict';

// 1689. Partitioning Into Minimum Number Of Deci-Binary Numbers: use the largest decimal digit as the necessary and sufficient layer count.
// O(d) time and O(1) auxiliary space, where d is the number of digits; inputs are read-only.
function solve(n) {
  let largest = 0;
  for (const digit of n) {
    largest = Math.max(largest, digit.charCodeAt(0) - 48);
    if (largest === 9) return largest;
  }
  return largest;
}

const minPartitions = solve;
class Solution {
  minPartitions(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minPartitions };
