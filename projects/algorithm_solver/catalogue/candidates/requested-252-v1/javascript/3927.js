/**
 * 3927. Minimize Array Sum Using Divisible Replacements
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimize-array-sum-using-divisible-replacements/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3927.Minimize%20Array%20Sum%20Using%20Divisible%20Replacements/README_EN.md
 * Complexity: O(M log M+n) time, O(M+n) space.
 * Each value reduces to the smallest originally present divisor, not necessarily the global minimum. Inputs preserved; native name pending.
 */

function solve(nums) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const present = new Set(nums);
  const smallest = new Int32Array(maximum + 1);
  for (let divisor = 1; divisor <= maximum; divisor += 1) {
    if (!present.has(divisor) || smallest[divisor] !== 0) continue;
    for (let multiple = divisor; multiple <= maximum; multiple += divisor) {
      if (smallest[multiple] === 0) smallest[multiple] = divisor;
    }
  }
  let answer = 0;
  for (const value of nums) answer += smallest[value];
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
