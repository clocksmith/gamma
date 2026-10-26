'use strict';

// 1363. Largest Multiple of Three: remove the fewest smallest digits needed modulo three; O(n) time and O(n) output space.

function solve(digits) {
  const counts = Array(10).fill(0);
  let sum = 0;
  for (const digit of digits) {
    counts[digit] += 1;
    sum += digit;
  }
  const remainder = sum % 3;
  if (remainder !== 0) {
    let single = -1;
    for (let digit = remainder; digit <= 9; digit += 3) {
      if (counts[digit] > 0) { single = digit; break; }
    }
    if (single !== -1) counts[single] -= 1;
    else {
      let needed = 2;
      for (let digit = 3 - remainder; digit <= 9; digit += 3) {
        const take = Math.min(needed, counts[digit]);
        counts[digit] -= take;
        needed -= take;
      }
      if (needed > 0) return '';
    }
  }
  const pieces = [];
  for (let digit = 9; digit >= 0; digit -= 1) pieces.push(String(digit).repeat(counts[digit]));
  const answer = pieces.join('');
  return answer.startsWith('0') ? '0' : answer;
}

const largestMultipleOfThree = solve;
class Solution {
  largestMultipleOfThree(digits) { return solve(digits); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestMultipleOfThree };
