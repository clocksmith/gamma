"use strict";
function Main(input) {
    let S = input.split("\n")[0].split(/\s/)[0] + 'X';
    let ans = 0, l = 0;
    for (let n = 0; n < S.length; n++) {
        switch (S.charAt(n)) {
        case 'A': 
        case 'C': 
        case 'T': 
        case 'G': 
            l += 1; 
            break;
        default: 
            if (l > ans) ans = l;
            l = 0;
        }
    }
    console.log(ans);
}
Main(require("fs").readFileSync("/dev/stdin", "utf8"));
