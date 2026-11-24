function main(input) {
  const tmp = input.trim().split(' ')
  const s = parseInt(tmp[0], 10)
  const w = parseInt(tmp[1], 10)

  if (w >= s) {
    console.log('unsafe')
  } else {
    console.log('safe')
  }
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'))