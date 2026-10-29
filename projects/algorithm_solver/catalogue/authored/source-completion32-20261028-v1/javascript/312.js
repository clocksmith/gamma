// 312 — Burst Balloons. Original implementation; authored candidate, not independently qualified.
function solve(nums) {
  const values = [1, ...nums, 1], n = values.length;
  const dp = Array.from({length: n}, () => Array(n).fill(0));
  // k is the LAST balloon removed from (left, right).
  for (let width = 2; width < n; width++) for (let left = 0; left + width < n; left++) {
    const right = left + width;
    for (let k = left + 1; k < right; k++) dp[left][right] = Math.max(dp[left][right], dp[left][k] + values[left] * values[k] * values[right] + dp[k][right]);
  }
  return dp[0][n - 1];
}

module.exports = { solve, maxCoins: solve };
