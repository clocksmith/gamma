"use strict"

function Main(input) {
    const N = parseInt(input[0], 10);
    const V = input.slice(1).map(v => parseInt(v, 10));

    let result = 0;

    for (let i = 0; i < N; i++) {
        result += 1 / V[i];
    }

    console.log(1 / result);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8").trim().split(/\n|\s/));