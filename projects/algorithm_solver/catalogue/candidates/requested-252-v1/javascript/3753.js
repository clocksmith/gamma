/**
 * 3753. Total Waviness of Numbers in Range II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/total-waviness-of-numbers-in-range-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3753.Total%20Waviness%20of%20Numbers%20in%20Range%20II/README_EN.md
 * Complexity: O(D*10^3) time and O(D*10^2) memo space, D decimal digits.
 * JavaScript returns BigInt; Python returns int. Use an explicitly approved decimal-string transport, not Number coercion.
 */

function solve(num1, num2) {
  function cumulative(bound) {
    if (bound < 1) return 0n;
    const digits = String(bound).split('').map(Number), memo = new Map();
    function visit(position, older, previous, tight) {
      if (position === digits.length) return [1n, 0n];
      const key = position + ',' + older + ',' + previous + ',' + tight;
      if (memo.has(key)) return memo.get(key);
      let count = 0n, total = 0n;
      const limit = tight ? digits[position] : 9;
      for (let digit = 0; digit <= limit; digit += 1) {
        const nextTight = tight && digit === limit;
        let result, added = false;
        if (previous === -1 && digit === 0) result = visit(position + 1, -1, -1, nextTight);
        else {
          result = visit(position + 1, previous, digit, nextTight);
          added = older !== -1 && ((previous > older && previous > digit) || (previous < older && previous < digit));
        }
        count += result[0]; total += result[1] + (added ? result[0] : 0n);
      }
      const result = [count, total]; memo.set(key, result); return result;
    }
    return visit(0, -1, -1, true)[1];
  }
  return cumulative(num2) - cumulative(num1 - 1);
}

function totalWaviness(num1, num2) {
  return solve(num1, num2);
}

class Solution {
  totalWaviness(num1, num2) {
    return solve(num1, num2);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, totalWaviness, Solution };
}
