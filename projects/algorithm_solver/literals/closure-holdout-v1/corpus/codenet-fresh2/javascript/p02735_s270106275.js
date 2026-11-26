"use strict"
const input = require("fs").readFileSync("/dev/stdin", "utf8")
;(input => {
    const rows = input.split("\n")
    const H = rows[0].split(" ")[0] - 0
    const W = rows[0].split(" ")[1] - 0

    const map = []
    const dp = []
    for (let r  = 0; r < H; r++) {
        map[r] = []
        dp[r] = []
        for (let c = 0; c <  W; c++) {
            map[r][c] = rows[r + 1][c]
            dp[r][c] = Infinity
        }
    }

    dp[0][0] = map[0][0] === '.' ? 0 : 1
    for (let r = 0; r < H; r++ ) {
        for (let c = 0; c < W; c++) {
            if (c + 1 < W) {
                if (map[r][c] === map[r][c + 1]) {
                    dp[r][c + 1] = Math.min(dp[r][c + 1], dp[r][c])
                } else {
                    dp[r][c + 1] = Math.min(dp[r][c + 1], dp[r][c] + 1)
                }
            }
            if (r + 1 < H) {
                if (map[r][c] === map[r + 1][c]) {
                    dp[r + 1][c] = Math.min(dp[r + 1][c], dp[r][c])
                } else {
                    dp[r + 1][c] = Math.min(dp[r + 1][c], dp[r][c] + 1)
                }
            }
        }
    }

    if (map[H - 1][W - 1] === '#') {
        dp[H - 1][W - 1]++
    }
    console.log(Math.ceil(dp[H - 1][W - 1] / 2))
})(input)
