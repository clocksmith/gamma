'use strict';

// 2466. Count Ways To Build Good Strings: count strings by their final appended block and sum the permitted lengths.
// O(high) time and O(high) auxiliary space; inputs are read-only.
function solve(low, high, zero, one) {
  const modulus = 1000000007;
  const ways = new Array(high + 1).fill(0);
  ways[0] = 1;
  let answer = 0;
  for (let length = 1; length <= high; length += 1) {
    if (length >= zero) ways[length] += ways[length - zero];
    if (length >= one) ways[length] += ways[length - one];
    ways[length] %= modulus;
    if (length >= low) answer = (answer + ways[length]) % modulus;
  }
  return answer;
}

const countGoodStrings = solve;
class Solution {
  countGoodStrings(low, high, zero, one) { return solve(low, high, zero, one); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGoodStrings };
