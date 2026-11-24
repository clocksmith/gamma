'use strict'

function main(o) {
  o = o.split('\n').map(v => ~~v)
  const k = o[5]
  const a = o.slice(0, 5)
  let i2 = 0
  for (let i = 0; i < a.length; i++) {
    for (let j = i + 1; j < a.length; j++) {
      if (a[j] - a[i] > k) {
        console.log(':(')
        return
      }
    //   console.log(a[j] - a[i])
    }
  }

  console.log('Yay!')
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'))
