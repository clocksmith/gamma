"use strict";
function main(input) {
    let line = input.split("\n");
    let arr = line[0].split(" ");
    const X = arr[0];
    const Y = arr[1];
    const Z = arr[2];
    console.log(Z, X, Y);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));