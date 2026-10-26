'use strict';

// 3490. Count Beautiful Numbers.
// Digit dynamic programming memoizes digit sum and exact product, distinguishing leading zeros from zero digits; O(10*S) time and O(S) space for reached states. Inputs are preserved.

function solve(l, r) {
  function countThrough(bound) {
    if (bound <= 0) return 0;
    const digits = String(bound).split('').map(Number), memo = new Map();
    function visit(position, total, product, tight) {
      if (position === digits.length) return total > 0 && product % total === 0 ? 1 : 0;
      const key = position + ',' + total + ',' + product + ',' + (tight ? 1 : 0);
      if (memo.has(key)) return memo.get(key);
      const limit = tight ? digits[position] : 9;
      let answer = 0;
      for (let digit = 0; digit <= limit; digit += 1) {
        const following = total === 0 && digit === 0 ? 1 : product * digit;
        answer += visit(position + 1, total + digit, following, tight && digit === limit);
      }
      memo.set(key, answer);
      return answer;
    }
    return visit(0, 0, 1, true);
  }
  return countThrough(r) - countThrough(l - 1);
}

const beautifulNumbers = solve;
class Solution {
  beautifulNumbers(l, r) { return solve(l, r); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, beautifulNumbers };
