'use strict';

// 2376. Count Special Integers. Count unique-digit prefixes using permutations; O(d^2+10*d) time and O(d) space for d decimal digits. Inputs are preserved.

function solve(n) {
  const digits = String(n).split('').map(Number);
  const size = digits.length;
  function permutations(available, count) {
    if (count > available) return 0;
    let ways = 1;
    for (let offset = 0; offset < count; offset += 1) ways *= available - offset;
    return ways;
  }
  let answer = 0;
  for (let length = 1; length < size; length += 1) answer += 9 * permutations(9, length - 1);
  let used = 0;
  for (let index = 0; index < size; index += 1) {
    const digit = digits[index];
    for (let smaller = index === 0 ? 1 : 0; smaller < digit; smaller += 1) {
      if ((used & (1 << smaller)) === 0) answer += permutations(9 - index, size - index - 1);
    }
    if ((used & (1 << digit)) !== 0) return answer;
    used |= 1 << digit;
  }
  return answer + 1;
}

const countSpecialNumbers = solve;
class Solution {
  countSpecialNumbers(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSpecialNumbers };
