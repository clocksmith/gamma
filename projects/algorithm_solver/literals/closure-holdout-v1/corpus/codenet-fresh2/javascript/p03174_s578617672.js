'use strict'

var mod = 1e9 + 7

function solve(N, mask, A, M, dp) {
  if (dp[N][mask] !== -1) {
    return dp[N][mask]
  } 
  if ((N === 0  && mask === 0) || (N === 0 && mask === (Math.pow(2, M) - 1))) {
    return 1
  }
  if (N === 0) {
    return 0
  }
  var res = 0 

  for (var i = 0; i < M; i++) {
    if (A[N-1][i] && !(mask & (1 << i))) {
      res = (res + solve(N-1, mask | (1 << i), A, M, dp)) % mod
    }
  }
  dp[N][mask] = res
  return res
}

function main(input) {
  var lines = input.split("\n")
  var N = parseInt(lines[0])
  var A = lines.slice(1).map(l => l.split(' ').map(e => parseInt(e)))
  var dp = new Array(N+1).fill(0).map(e => new Array(Math.pow(2,N)).fill(-1))
  dp[0][0] = 1
  dp[0][(1 << N) - 1] = 1
  var ans = solve(N, 0, A, N, dp)
  console.log(ans)
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));

// 6

// 0 1 1
// 1 0 1
// 1 1 1

// dp[0][111] = 1
// dp[3][000] = sum(dp[2][001] + dp[2][010] + dp[2][100])
// dp[2][001] = sum(dp[1][011] + dp[1][101])
// dp[2][010] = sum(dp[1][110] + dp[1][011])
// dp[2][100] = sum(dp[1][110] + dp[1][101])
// dp[1][011] = sum(dp[0][111])

//   0 1 2 3 4 5 6 7
// 0 1 0 0 0 0 0 0 1
// 1 0 0 0 1 0 1 0 0
// 2 0 1 1 0 1 0 0 0
// 3 3
