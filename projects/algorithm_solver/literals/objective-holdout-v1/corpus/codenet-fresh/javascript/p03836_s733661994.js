'use strict'

function main(input) {
  input = input
    .trim()
    .split(' ')
    .map(Number)
  const sx = input[0]
  const sy = input[1]
  const tx = input[2]
  const ty = input[3]

  const dx = tx - sx
  const dy = ty - sy

  let ans = ''
  for (let i = 0; i < dy; i++) {
    ans += 'U'
  }
  for (let i = 0; i < dx; i++) {
    ans += 'R'
  }

  for (let i = 0; i < dy; i++) {
    ans += 'D'
  }
  for (let i = 0; i < dx; i++) {
    ans += 'L'
  }

  ans += 'L'
  for (let i = 0; i < dy + 1; i++) {
    ans += 'U'
  }
  for (let i = 0; i < dx + 1; i++) {
    ans += 'R'
  }
  ans += 'DR'
  for (let i = 0; i < dy + 1; i++) {
    ans += 'D'
  }
  for (let i = 0; i < dx + 1; i++) {
    ans += 'L'
  }
  ans += 'U'

  console.log(ans)
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'))
