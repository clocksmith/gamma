const check = (word, used) => {
  if (used.length === 0) {
    return true
  }

  if (used[used.length - 1][used[used.length - 1].length - 1] !== word[0]) {
    return false
  }

  if (used.includes(word)) {
    return false
  }

  return true
}

const main = stdin => {
  const input = stdin.trim().split('\n')
  const N = parseInt(input[0])

  const used = []
  let ans = true
  for (let i = 0; i < N; i++) {
    const word = input[i + 1]
    if (!check(word, used)) {
      ans = false
      break
    }

    used.push(word)
  }

  console.log(ans ? 'Yes' : 'No')
}


// 標準入力
main(require("fs").readFileSync("/dev/stdin", "utf8"))
