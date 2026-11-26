'use strict';

function Main(INPUT) {
    const input = INPUT.split("\n")[0].split(" ").map(n => Number(n));
    input.sort((a, b) => a - b);

    console.log(input[0] + input[1]);
}

Main(require("fs").readFileSync("/dev/stdin", "utf8"));
