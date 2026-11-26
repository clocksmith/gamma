"use strict";
function main(input) {
    const r = input.replace("\n", "");
    console.log(r ** 2);
    return;
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));