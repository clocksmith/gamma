'use strict';

// 2489. Number of Substrings With Fixed Ratio: count equal zero/one weighted prefix balances.
// O(n) expected time and O(n) auxiliary space on the stated integer domain; inputs are read-only.
function solve(s, num1, num2) {
  const frequencies = new Map([[0, 1]]);
  let balance = 0;
  let answer = 0;
  for (const char of s) {
    balance += char === '0' ? num2 : -num1;
    answer += frequencies.get(balance) || 0;
    frequencies.set(balance, (frequencies.get(balance) || 0) + 1);
  }
  return answer;
}

const fixedRatio = solve;
class Solution {
  fixedRatio(s, num1, num2) { return solve(s, num1, num2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fixedRatio };
