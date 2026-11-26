'use strict'
// import bigInt from 'big-integer'

const main = (input) => {
    input = input.trim()
    const nums = input.split("")
    const plusNum = nums.length - 1
    let answer = 0

    for (let bit = 0; bit < (1 << plusNum); bit++) {
        let tmpStrs = [nums[0]]
        for (let i = 0; i < plusNum; i++) {
            const num = nums[i + 1]
            if (bit & (1 << i)) {
                tmpStrs.push(num)
            } else {
                tmpStrs[tmpStrs.length - 1] += num
            }
        }
        answer += tmpStrs.reduce((acc, cur) => acc + parseInt(cur, 10), 0)
    }

    console.log(answer)
}

main(require('fs').readFileSync('/dev/stdin', 'utf8'));
