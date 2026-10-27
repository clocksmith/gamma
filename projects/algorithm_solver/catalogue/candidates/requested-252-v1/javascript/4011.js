/**
 * 4011. Count Subarrays With Even Odd Ratio I
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-subarrays-with-even-odd-ratio-i/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4011.Count%20Subarrays%20With%20Even%20Odd%20Ratio%20I/README_EN.md
 * Complexity: O(n log n) time, O(n) space.
 * Map odds to +a and evens to -b. Nonnegative interval sums automatically exclude all-even nonempty intervals. Counts and prefix sums stay within Number exact range. Inputs preserved; native method unconfirmed.
 */

function solve(nums, a, b) {
  const prefix = [0];
  for (const value of nums) prefix.push(prefix[prefix.length - 1] + (value % 2 ? a : -b));
  const values = Array.from(new Set(prefix)).sort((x, y) => x - y);
  const rank = new Map(values.map((value, i) => [value, i + 1])), tree = new Int32Array(values.length + 1);
  let answer = 0;
  for (const value of prefix) {
    let i = rank.get(value);
    for (; i > 0; i -= i & -i) answer += tree[i];
    for (i = rank.get(value); i < tree.length; i += i & -i) tree[i]++;
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
