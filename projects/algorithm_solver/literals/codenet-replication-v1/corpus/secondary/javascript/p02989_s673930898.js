"use strict"
function main(arg) {
    arg = arg.trim().split("\n")[1].split(' ').map(Number).sort((a,b) => a- b)
    const n = arg.length
    const c = n / 2
    // console.log(arg[c-1]) 
    // console.log(arg) 
    let min = arg[c-1]
    let max = arg[c]
    let ans = 0
    for (let i = max; i > min; i--) {
        ans++
    }
    console.log(ans) 
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));