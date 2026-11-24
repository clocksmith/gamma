'use strict'

function main(input) {
  input = input.trim().split('\n')
  const img = input.slice(1)

  let tmp = []
  for (let i = 0; i < img.length; i++) {
    tmp.push(img[i])
    tmp.push(img[i])
  }

  console.log(tmp.join('\n'))
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'))
