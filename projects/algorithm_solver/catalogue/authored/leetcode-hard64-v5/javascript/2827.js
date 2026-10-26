'use strict';

// 2827. Number of Beautiful Integers in the Range. Digit DP over parity balance, divisibility, and leading zeros; O(10*d^2*k) time and O(d^2*k) space for d decimal digits. Inputs are preserved.

function solve(low, high, k) {
  function through(bound) {
    if (bound <= 0) return 0;
    const digits = String(bound).split('').map(Number);
    const width = 2 * digits.length + 1;
    const memo = new Map();
    function visit(index, balance, remainder, tight, started) {
      if (index === digits.length) return Number(started && balance === 0 && remainder === 0);
      if (Math.abs(balance) > digits.length - index) return 0;
      const key = (((index * width + balance + digits.length) * k + remainder) * 2 + Number(tight)) * 2 + Number(started);
      if (memo.has(key)) return memo.get(key);
      let answer = 0;
      const upper = tight ? digits[index] : 9;
      for (let digit = 0; digit <= upper; digit += 1) {
        const nextTight = tight && digit === upper;
        if (!started && digit === 0) {
          answer += visit(index + 1, 0, 0, nextTight, false);
        } else {
          const nextBalance = balance + (digit % 2 === 1 ? 1 : -1);
          answer += visit(index + 1, nextBalance, (remainder * 10 + digit) % k, nextTight, true);
        }
      }
      memo.set(key, answer);
      return answer;
    }
    return visit(0, 0, 0, true, false);
  }
  return through(high) - through(low - 1);
}

const numberOfBeautifulIntegers = solve;
class Solution {
  numberOfBeautifulIntegers(low, high, k) { return solve(low, high, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfBeautifulIntegers };
