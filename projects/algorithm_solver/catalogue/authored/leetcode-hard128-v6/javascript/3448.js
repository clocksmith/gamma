'use strict';

// 3448. Count Substrings Divisible By Last Digit.
// Maintain suffix remainder counts independently for divisors one through nine; O(45*n) time and O(45) working space. Input is preserved.

function solve(s) {
  const counts = Array.from({ length: 10 }, (_, divisor) => Array(divisor).fill(0));
  let answer = 0;
  for (const character of s) {
    const digit = Number(character);
    for (let divisor = 1; divisor <= 9; divisor += 1) {
      const following = Array(divisor).fill(0);
      following[digit % divisor] = 1;
      for (let remainder = 0; remainder < divisor; remainder += 1) following[(10 * remainder + digit) % divisor] += counts[divisor][remainder];
      counts[divisor] = following;
    }
    if (digit !== 0) answer += counts[digit][0];
  }
  return answer;
}

const countSubstrings = solve;
class Solution {
  countSubstrings(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubstrings };
