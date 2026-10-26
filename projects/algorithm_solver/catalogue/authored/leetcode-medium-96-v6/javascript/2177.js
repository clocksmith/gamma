'use strict';

// 2177. Find Three Consecutive Integers That Sum to a Given Number: use the integer average as the unique middle value.
// O(1) time and O(1) result space on the bounded integer domain; inputs are read-only.
function solve(num) {
  if (num % 3 !== 0) return [];
  const middle = num / 3;
  return [middle - 1, middle, middle + 1];
}

const sumOfThree = solve;
class Solution {
  sumOfThree(num) { return solve(num); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfThree };
