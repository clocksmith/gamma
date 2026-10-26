'use strict';

// 1987. Number of Unique Good Subsequences. Distinct valid subsequences grouped by final bit; O(n) time and O(1) space. Inputs are preserved.

function solve(binary) {
  const modulus = 1000000007;
  let endingZero = 0;
  let endingOne = 0;
  let hasZero = 0;
  for (const digit of binary) {
    if (digit === '1') {
      endingOne = (endingZero + endingOne + 1) % modulus;
    } else {
      endingZero = (endingZero + endingOne) % modulus;
      hasZero = 1;
    }
  }
  return (endingZero + endingOne + hasZero) % modulus;
}

const numberOfUniqueGoodSubsequences = solve;
class Solution {
  numberOfUniqueGoodSubsequences(binary) { return solve(binary); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfUniqueGoodSubsequences };
