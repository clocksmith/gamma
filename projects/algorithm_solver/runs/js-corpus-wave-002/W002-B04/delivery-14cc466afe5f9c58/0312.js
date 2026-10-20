function maxCoins(nums) {
  const balloons = [1, ...nums, 1];
  const n = balloons.length;
  const dp = Array.from({ length: n }, () => Array(n).fill(0));
  for (let length = 2; length < n; length++) {
    for (let left = 0; left + length < n; left++) {
      const right = left + length;
      for (let last = left + 1; last < right; last++) {
        dp[left][right] = Math.max(dp[left][right], dp[left][last] + dp[last][right] + balloons[left] * balloons[last] * balloons[right]);
      }
    }
  }
  return dp[0][n - 1];
}
