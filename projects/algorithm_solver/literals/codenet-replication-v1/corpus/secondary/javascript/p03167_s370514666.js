'use strict'

var mod = 1e9 + 7

function solve(H, W, M) {
  var dp = new Array(H).fill(0).map(e => new Array(W).fill(1))
  for (var i = 0; i < H; i++) {
    for (var j = 0; j < W; j++) {
      if (i === 0 && j === 0) {
        dp[i][j] = 1
        continue
      }
      if (M[i][j] === '#') {
        dp[i][j] = 0
        continue
      }
      var left = (j-1) >= 0 ? dp[i][j-1] : 0
      var up = (i-1) >= 0 ? dp[i-1][j] : 0
      dp[i][j] = (left + up) % mod
    }
  }
  return dp[H-1][W-1] % mod
}

function main(input) {
  var lines = input.split("\n")
  var HW = lines[0].split(' ').map(i => parseInt(i))
  var H = HW[0]
  var W = HW[1]
  var M = lines.slice(1)
  var ans = solve(H, W, M)
  console.log(ans)
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));