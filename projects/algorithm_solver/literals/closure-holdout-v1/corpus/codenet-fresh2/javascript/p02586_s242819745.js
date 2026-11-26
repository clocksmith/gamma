function Main(input) {
  input = input.trim().split("\n");
  const [R, C, n] = input.shift().split(" ").map((a) => parseInt(a, 10));
  const values = input.map((a) => a.split(" ").map((b) => parseInt(b, 10)));

  let i, j, k;
  a = [];
  dp = [];

  for (let i=0; i<n; i++) {
    const [r, c, v] = values[i];
    a[r - 1] = a[r - 1] || [];
    a[r - 1][c - 1] = v;
  }

  for (i=0; i<R; i++) {
    dp[i] = dp[i] || [];
    dp[i+1] = dp[i+1] || [];
    for (j=0; j<C; j++) {
      dp[i][j] = dp[i][j] || [0, 0, 0, 0];
      dp[i][j+1] = dp[i][j+1] || [0, 0, 0, 0];
      dp[i+1][j] = dp[i][j] || [0, 0, 0, 0];
      for (k = 2; k >= 0; k--) {
        dp[i][j][k+1] = Math.max(dp[i][j][k+1], dp[i][j][k]  + (a[i] && a[i][j] || 0));
      }
      for (k = 0; k<4; k++) {
        dp[i+1][j][0] = Math.max(dp[i+1][j][0], dp[i][j][k]);
        dp[i][j+1][k] = Math.max(dp[i][j+1][k], dp[i][j][k]);
      }
    }
  }

  let ans = 0;
  for (k = 0; k<4; k++) {
    ans = Math.max(ans, dp[R-1][C-1][k]);
  }
  console.log(ans);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
