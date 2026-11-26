"use strict";
function Main(input) {
    let lines = input.split("\n");
    let NQ = lines.shift().trim().split(/\s/).map((v) => v - 0);
    let N = NQ[0], Q = NQ[1];
    let S = lines.shift().trim();
    let left = 0;
    let right = N - 1;
    for (let n = Q-1; n >= 0; n--) {
        let td = lines[n].trim().split(/\s/);
        let t = td[0], d = td[1];
        if      (S.charAt(left-1 ) === t && d === "R") left--;
        else if (S.charAt(left   ) === t && d === "L") left++;
        if      (S.charAt(right  ) === t && d === "R") right--;
        else if (S.charAt(right+1) === t && d === "L") right++;
        if (left > right) break;
    }
    console.log(right - left + 1);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));