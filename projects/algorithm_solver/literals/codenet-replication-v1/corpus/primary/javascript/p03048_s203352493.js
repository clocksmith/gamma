'use strict'

function Main(input) {
  const R = Number(input.split(" ")[0])
  const G = Number(input.split(" ")[1])
  const B = Number(input.split(" ")[2])
  const N = Number(input.split(" ")[3])

  const nums = [R, G, B].sort((x, y) => y - x)

  const max = nums[0]
  const min = nums[1]
  const mid = nums[2]

  const maxDivided = Math.floor(N / max)

  let ans = 0
  for (let i=0; i<=maxDivided; i++) {
    const midDivided = Math.floor((N - (i * max)) / mid)
    for (let j=0; j<=midDivided; j++) {
      const reminder = N - (i * max) - (j * mid)
      if (reminder % min === 0) {
        ans++
      }
    }
  }

  console.log(ans)
}

Main(require("fs").readFileSync("/dev/stdin", "utf8").trim())
