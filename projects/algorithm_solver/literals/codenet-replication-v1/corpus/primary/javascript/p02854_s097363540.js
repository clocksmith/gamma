"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const N = parseInt(arg[0]);
    const A = arg[1].split(" ").map(n=>parseInt(n));
    
    let s = Array(N + 1).fill(0);
    let sum = A.reduce((m,n)=>m+n);
    
    for(let i in A) {
        s[parseInt(i) + 1] = A[i] + s[i];
    }
    
    let costs = Infinity;
    
    for(let i=1; i<A.length; i++) {
        // console.log("A[i-1]" + A[i-1]);
        // console.log("sum - s[i]" + (sum - s[i]));
        
        costs = Math.min(costs, Math.abs(s[i] - (sum - s[i])));
    }

    console.log(costs);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));