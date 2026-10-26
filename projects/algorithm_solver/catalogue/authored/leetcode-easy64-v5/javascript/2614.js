'use strict';

// 2614. Prime In Diagonal (Easy).
// Specification: https://leetcode.com/problems/prime-in-diagonal/description/
// O(n * sqrt(M)) time, O(1) auxiliary space; preserve the matrix.
function solve(nums) {
  function isPrime(value) {
    if (value < 2) return false;
    if (value % 2 === 0) return value === 2;
    for (let divisor = 3; divisor * divisor <= value; divisor += 2) {
      if (value % divisor === 0) return false;
    }
    return true;
  }
  let largest = 0;
  const size = nums.length;
  for (let row = 0; row < size; row++) {
    const primary = nums[row][row];
    const secondary = nums[row][size - row - 1];
    if (primary > largest && isPrime(primary)) largest = primary;
    if (secondary > largest && isPrime(secondary)) largest = secondary;
  }
  return largest;
}

const diagonalPrime = solve;
class Solution {
  diagonalPrime(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, diagonalPrime };
