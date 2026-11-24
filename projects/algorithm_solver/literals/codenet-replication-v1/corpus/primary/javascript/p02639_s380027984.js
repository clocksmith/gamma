"use strict";

const main = arg => {
    const input = arg.trim().split("\n");

    const x = input[0].split(" ").map(n => parseInt(n));
    for(let i = 0; i<5; i++){
        if(x[i] == 0) console.log(i+1)
    }
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));  