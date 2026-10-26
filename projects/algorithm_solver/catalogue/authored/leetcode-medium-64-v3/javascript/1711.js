'use strict';

// 1711. Count Good Meals: count earlier complements for each possible power-of-two sum.
// O(22 * n) time and O(n) auxiliary space on the stated value domain; inputs are read-only.
function solve(deliciousness) {
  const frequencies = new Map();
  let answer = 0;
  const modulus = 1000000007;
  for (const value of deliciousness) {
    for (let power = 1; power <= 2097152; power *= 2) {
      answer = (answer + (frequencies.get(power - value) || 0)) % modulus;
    }
    frequencies.set(value, (frequencies.get(value) || 0) + 1);
  }
  return answer;
}

const countPairs = solve;
class Solution {
  countPairs(deliciousness) { return solve(deliciousness); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
