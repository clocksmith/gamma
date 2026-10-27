/**
 * 3791. Number of Balanced Integers in a Range
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/number-of-balanced-integers-in-a-range/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3791.Number%20of%20Balanced%20Integers%20in%20a%20Range/README_EN.md
 * Complexity: O(D^2*100) time; O(D^2*10) memo space.
 * Leading zero padding can only negate the parity difference; equality is invariant. Excludes zero; no positive one-digit number qualifies.
 */

function solve(low, high) {
  function cumulative(bound) {
    if (bound < 1) return 0;
    const digits = String(bound).split('').map(Number), memo = new Map();
    function count(position, difference, tight) {
      if (position === digits.length) return difference === 0 ? 1 : 0;
      const key = position + ',' + difference + ',' + tight;
      if (memo.has(key)) return memo.get(key);
      const limit = tight ? digits[position] : 9, sign = position % 2 === 0 ? 1 : -1;
      let result = 0;
      for (let digit = 0; digit <= limit; digit += 1) result += count(position + 1, difference + sign * digit, tight && digit === limit);
      memo.set(key, result); return result;
    }
    return count(0, 0, true) - 1;
  }
  return cumulative(high) - cumulative(low - 1);
}

function countBalanced(low, high) {
  return solve(low, high);
}

class Solution {
  countBalanced(low, high) {
    return solve(low, high);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countBalanced, Solution };
}
