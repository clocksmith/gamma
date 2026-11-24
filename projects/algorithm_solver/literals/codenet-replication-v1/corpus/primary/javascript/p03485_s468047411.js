'use strict'

function main(input) {

    const sum = input.split(/\s/).map(v => ~~v).reduce((a, b) => a + b)

    const ans = Math.ceil(sum / 2)

    console.log(ans)
}
main(require("fs").readFileSync("/dev/stdin", "utf8"));
