'use strict';

// 2801. Count Stepping Numbers in Range. Rolling digit DP with a separate not-started state; O(110*d) time and O(1) auxiliary space for d decimal digits. Inputs are preserved.

function solve(low, high) {
  const modulus = 1000000007;
  function through(bound) {
    let counts = Array.from({ length: 2 }, () => Array(11).fill(0));
    counts[1][10] = 1;
    for (let index = 0; index < bound.length; index += 1) {
      const ceiling = bound.charCodeAt(index) - 48;
      const following = Array.from({ length: 2 }, () => Array(11).fill(0));
      for (let tight = 0; tight < 2; tight += 1) {
        for (let previous = 0; previous <= 10; previous += 1) {
          const ways = counts[tight][previous];
          if (ways === 0) continue;
          const upper = tight === 1 ? ceiling : 9;
          for (let digit = 0; digit <= upper; digit += 1) {
            const nextTight = Number(tight === 1 && digit === ceiling);
            let nextDigit;
            if (previous === 10 && digit === 0) nextDigit = 10;
            else if (previous === 10 || Math.abs(previous - digit) === 1) nextDigit = digit;
            else continue;
            following[nextTight][nextDigit] = (following[nextTight][nextDigit] + ways) % modulus;
          }
        }
      }
      counts = following;
    }
    let answer = 0;
    for (let tight = 0; tight < 2; tight += 1) {
      for (let digit = 0; digit < 10; digit += 1) answer = (answer + counts[tight][digit]) % modulus;
    }
    return answer;
  }
  let lowIsStepping = 1;
  for (let index = 1; index < low.length; index += 1) {
    if (Math.abs(low.charCodeAt(index) - low.charCodeAt(index - 1)) !== 1) { lowIsStepping = 0; break; }
  }
  return (through(high) - through(low) + lowIsStepping + modulus) % modulus;
}

const countSteppingNumbers = solve;
class Solution {
  countSteppingNumbers(low, high) { return solve(low, high); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSteppingNumbers };
