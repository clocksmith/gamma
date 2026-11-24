"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const N = parseInt(arg[0]);
    const d = arg[1].split(" ").map(n=>parseInt(n));
    
    let answer = 0;
    
    for(let i in d) {
        for(let j= ~~i + 1; j<N; j++) {
            // console.log((d[i] * d[j]))
            answer += (d[i] * d[j]);
        }
    }
    
    console.log(answer);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));