'use strict'

const Main = (input) => {
  const nr = input.split('\n')
  const N = parseInt(nr[0])
  let answer = 0
  for (let i = 0; i < N; i++) {
    const a = parseInt(nr[1].split(' ')[i])
    if ((a % 2 === 0) && ((a % 3 !== 0) && (a % 5 !== 0))) {
      answer = 1
      break
    }
  }
  if (answer === 0) {
    console.log('APPROVED')
  } else {
    console.log('DENIED')
  }
}

Main(require('fs').readFileSync('/dev/stdin', 'utf8'))
