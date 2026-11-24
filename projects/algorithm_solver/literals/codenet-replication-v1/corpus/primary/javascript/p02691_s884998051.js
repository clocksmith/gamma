"use strict";
var input = require("fs").readFileSync("/dev/stdin", "utf8");
var cin = input.trim().split(/ |\n/), cid = 0;

main();

function main() {
    //console.log(cin);
    //   cin = cin.map(i => +i);
    let n = +cin.shift();
    let B = {};
    let C = {};
    cin.forEach((v, i) => {
        const x = Number(v);
        B[i + 1 + x] = B[i + 1 + x] + 1 || 1;
        C[i + 1 - x] = C[i + 1 - x] + 1 || 1;
    });
    //console.log({ B, C })
    let keys = Object.keys(B);
    let ans = 0;
    keys.filter(i => C[i]).forEach(i => {
        ans += (B[i] * C[i]);
        //console.log(i, B[i], C[i]);
    });


    console.log(ans);
}