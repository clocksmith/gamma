"use strict";
function main(input) {
    const line = input.split("\n");
    let arr = line[0].split(" ");
    const N = arr[0];
    const A = arr[1];
    const B = arr[2];
    console.log(Math.min(A * N, B));
    return;
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));