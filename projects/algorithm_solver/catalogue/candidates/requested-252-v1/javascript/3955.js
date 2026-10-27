/**
 * 3955. Valid Binary Strings With Cost Limit
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/valid-binary-strings-with-cost-limit/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3955.Valid%20Binary%20Strings%20With%20Cost%20Limit/README_EN.md
 * Complexity: O(n*2^n) worst-case output time and space, recursion depth n <= 12.
 * Outputs lexicographic order, which is an allowed deterministic order. Inputs preserved.
 */

function solve(n, k) {
  const answer = [];
  function visit(prefix, cost) {
    const position = prefix.length;
    if (position === n) { answer.push(prefix); return; }
    visit(prefix + '0', cost);
    if ((position === 0 || prefix[position - 1] === '0') && cost + position <= k) visit(prefix + '1', cost + position);
  }
  visit('', 0);
  return answer;
}

function generateValidStrings(n, k) {
  return solve(n, k);
}

class Solution {
  generateValidStrings(n, k) {
    return solve(n, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, generateValidStrings, Solution };
}
