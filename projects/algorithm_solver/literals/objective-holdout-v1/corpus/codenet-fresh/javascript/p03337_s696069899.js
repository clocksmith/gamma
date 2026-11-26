function main(input) {
  const tmp = input.trim().split(' ')
  const a = parseInt(tmp[0], 10)
  const b = parseInt(tmp[1], 10)

  let answer = Math.max(a + b, a - b, a * b)
  if (answer == 0) {
    console.log(0)
  } else {
    console.log(answer)
  }
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'))