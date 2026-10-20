function numSquares(n) {
  const dp = Array(n + 1).fill(Infinity);
  dp[0] = 0;
  for (let value = 1; value <= n; value++) {
    for (let square = 1; square * square <= value; square++) {
      dp[value] = Math.min(dp[value], dp[value - square * square] + 1);
    }
  }
  return dp[n];
}
