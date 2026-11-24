"use strict";

function main(arg) {
    const N = arg.split("\n")[0].split("").map(n=>parseInt(n));

    if(N[0] == N[1] && N[1] == N[2] || N[1] == N[2] && N[2] == N[3]) {
        console.log("Yes");
    } else {
        console.log("No");
    }
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));