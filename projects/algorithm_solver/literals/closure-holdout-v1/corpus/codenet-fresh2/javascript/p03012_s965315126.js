'use strict'
function main(input) {
    const tmp = input.split('\n');
    const N = parseInt(tmp[0], 10);
    const W = tmp[1].split(' ').map((elem) => parseInt(elem, 10));
    let leftSum = 0;
    let rightSum = W.reduce((sum, elem) => sum + elem);
    let absVal = [];

    for (let T = 1; T < N; T++) {
        leftSum += W[T - 1];
        rightSum -= W[T - 1];
        absVal.push(Math.abs(rightSum - leftSum));
    }
    const smallestAbs = absVal.reduce((min, elem) => Math.min(min, elem));
    console.log(smallestAbs);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));