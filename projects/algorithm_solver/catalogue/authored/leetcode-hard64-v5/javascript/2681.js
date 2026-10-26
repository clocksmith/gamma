'use strict';

// 2681. Power of Heroes. Accumulate contributions by maximum with a running sum of subset minima; O(n log n) time and O(n) space. Inputs are preserved.

function solve(nums) {
  const modulus = 1000000007n;
  let minima = 0n;
  let answer = 0n;
  for (const number of nums.slice().sort((a, b) => a - b)) {
    const value = BigInt(number);
    answer = (answer + value * value % modulus * (value + minima)) % modulus;
    minima = (2n * minima + value) % modulus;
  }
  return Number(answer);
}

const sumOfPower = solve;
class Solution {
  sumOfPower(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfPower };
