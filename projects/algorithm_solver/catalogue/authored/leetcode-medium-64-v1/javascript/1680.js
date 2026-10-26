'use strict';

// 1680. Concatenation of Consecutive Binary Numbers: append each integer using its current binary place multiplier.
// O(n) time and O(1) auxiliary space under n <= 100000; inputs are read-only.
function solve(n) {
  const modulus = 1000000007;
  let multiplier = 1;
  let answer = 0;
  for (let value = 1; value <= n; value += 1) {
    if ((value & (value - 1)) === 0) multiplier *= 2;
    // Multiplication stays exact below 2^53; a bitwise shift would truncate.
    answer = (answer * multiplier + value) % modulus;
  }
  return answer;
}

const concatenatedBinary = solve;
class Solution {
  concatenatedBinary(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, concatenatedBinary };
