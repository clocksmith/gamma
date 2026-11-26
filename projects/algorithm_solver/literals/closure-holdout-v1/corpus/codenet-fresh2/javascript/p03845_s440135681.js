'use strict'

const main = (input) => {
    input = input.split('\n')
    const T = input[1].split(' ').map(v => parseInt(v))
    const M = parseInt(input[2])
    const P = input.slice(3, 3 + M)
    P.forEach(v => {
        let index = parseInt(v.split(' ')[0]) - 1
        let num = parseInt(v.split(' ')[1])
        let sum = 0
        T.forEach((v, i) => {
            if(i === index){
                sum += num
            }else{
                sum += v
            }
        })
        console.log(sum)
    })
}

main(require('fs').readFileSync('/dev/stdin', 'utf-8'))