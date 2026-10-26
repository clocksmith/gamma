'use strict';

// 2484. Count Palindromic Subsequences. Count reversed digit-pair combinations on each side of the center; O(100*n) time and O(100) space. Inputs are preserved.

function solve(s) {
  const modulus = 1000000007;
  const leftSingle = Array(10).fill(0);
  const rightSingle = Array(10).fill(0);
  const leftPairs = Array.from({ length: 10 }, () => Array(10).fill(0));
  const rightPairs = Array.from({ length: 10 }, () => Array(10).fill(0));
  for (let index = s.length - 1; index >= 0; index -= 1) {
    const digit = s.charCodeAt(index) - 48;
    for (let other = 0; other < 10; other += 1) rightPairs[digit][other] += rightSingle[other];
    rightSingle[digit] += 1;
  }
  let answer = 0;
  for (let index = 0; index < s.length; index += 1) {
    const digit = s.charCodeAt(index) - 48;
    rightSingle[digit] -= 1;
    for (let other = 0; other < 10; other += 1) rightPairs[digit][other] -= rightSingle[other];
    for (let first = 0; first < 10; first += 1) {
      for (let second = 0; second < 10; second += 1) {
        // With n <= 10000, each pair-count product is below Number's exact-integer limit.
        answer = (answer + leftPairs[first][second] * rightPairs[second][first]) % modulus;
      }
    }
    for (let other = 0; other < 10; other += 1) leftPairs[other][digit] += leftSingle[other];
    leftSingle[digit] += 1;
  }
  return answer;
}

const countPalindromes = solve;
class Solution {
  countPalindromes(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPalindromes };
