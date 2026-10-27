/**
 * 3957. Maximum Sum of M Non-Overlapping Subarrays II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-sum-of-m-non-overlapping-subarrays-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3957.Maximum%20Sum%20of%20M%20Non-Overlapping%20Subarrays%20II/README_EN.md
 * Complexity: O(n*min(m,floor(n/l))) time and O(n) space; exact layer DP with a sliding maximum.
 * At least one subarray is required, including all-negative input. Inputs preserved. Native judge method pending. PERFORMANCE LIMITATION: quadratic worst case at n=100000; full-size time-limit suitability is not established. This is a complete exact algorithm, not a claimed fast solution to the largest instances.
 */

function solve(nums, m, l, r) {
  const n = nums.length;
  const prefix = new Float64Array(n + 1);
  for (let index = 0; index < n; index++) prefix[index + 1] = prefix[index] + nums[index];
  let previous = new Float64Array(n + 1);
  let answer = -Infinity;
  for (let count = 1; count <= Math.min(m, Math.floor(n / l)); count++) {
    const current = new Float64Array(n + 1).fill(-Infinity);
    const queueIndex = new Int32Array(n + 1);
    const queueValue = new Float64Array(n + 1);
    let head = 0;
    let tail = 0;
    for (let end = 1; end <= n; end++) {
      const start = end - l;
      if (start >= 0 && previous[start] !== -Infinity) {
        const value = previous[start] - prefix[start];
        while (tail > head && queueValue[tail - 1] <= value) tail--;
        queueIndex[tail] = start;
        queueValue[tail++] = value;
      }
      while (head < tail && queueIndex[head] < end - r) head++;
      current[end] = current[end - 1];
      if (head < tail) current[end] = Math.max(current[end], prefix[end] + queueValue[head]);
    }
    answer = Math.max(answer, current[n]);
    previous = current;
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
