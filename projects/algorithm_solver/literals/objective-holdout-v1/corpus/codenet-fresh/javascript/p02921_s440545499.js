const main = stdin => {
  const input = stdin.trim().split('\n')

  const S = input[0]
  const T = input[1]

  let count = 0
  for (let i = 0; i < 3; i++) {
    if (S[i] === T[i]) {
      count++
    }
  }

  console.log(count)
}

// 標準入力
main(require("fs").readFileSync("/dev/stdin", "utf8"))
