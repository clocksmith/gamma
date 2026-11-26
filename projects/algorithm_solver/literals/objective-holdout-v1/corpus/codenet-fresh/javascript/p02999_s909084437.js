"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const X = parseInt(arg[0].split(" ")[0]);
    const A = parseInt(arg[0].split(" ")[1]);
    console.log(X < A ? 0 : 10);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));