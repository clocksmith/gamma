"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const N = parseInt(arg[0].split(" ")[0]);
    const K = parseInt(arg[0].split(" ")[1]);
    
    let answer = 0;
    
    if(K === 0) {
        console.log(N * N);
        return;
    }
    
    for(let b=1; b<=N; b++) {
        answer += Math.floor(N / b) * Math.max(0, b - K);
        
        if(N % b > 0) {
            answer += Math.max(0, (N % b) - K + 1);
        }
    }
    
    console.log(answer);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));