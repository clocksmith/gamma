'use strict';

// 476. Number Complement (Easy).
// Specification: https://leetcode.com/problems/number-complement/description/
// O(log num) time, O(1) space; complement only significant bits of a positive integer.
function solve(num) {
  let boundary = 1;
  while (boundary <= num) boundary *= 2;
  return boundary - 1 - num;
}

const findComplement = solve;
class Solution {
  findComplement(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findComplement };
