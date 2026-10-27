/**
 * 3954. Sum of Compatible Numbers in Range I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/sum-of-compatible-numbers-in-range-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3954.Sum%20of%20Compatible%20Numbers%20in%20Range%20I/README_EN.md
 * Complexity: O(k) time, O(1) space.
 * Positive candidates only; n,k <= 100. Inputs preserved.
 */

function solve(n, k) {
  let answer = 0;
  for (let value = Math.max(1, n - k); value <= n + k; value++) {
    if ((n & value) === 0) answer += value;
  }
  return answer;
}

function sumOfGoodIntegers(n, k) {
  return solve(n, k);
}

class Solution {
  sumOfGoodIntegers(n, k) {
    return solve(n, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, sumOfGoodIntegers, Solution };
}
