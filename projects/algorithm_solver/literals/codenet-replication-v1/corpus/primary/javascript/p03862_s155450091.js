"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const N = parseInt(arg[0].split(" ")[0]);
    const X = parseInt(arg[0].split(" ")[1]);
    
    const A = arg[1].split(" ").map(n=>parseInt(n));
    let cnt = 0;
    
    for(let i=0; i<N-1; i++) {
        let sum = A[i] + A[i + 1];

        if(sum > X) {
            // let temp;
            // if(A[i+1] > A[i]) {
            //     temp = A[i+1]  - X;
            //     A[i+1] -= temp;
            // } else {
            //     temp = A[i] - X;
            //     A[i] -= temp;
            // }
            
            // A[i+1]--;
            
            A[i+1] = Math.max(0, A[i+1] - (sum - X));
            
            cnt += sum - X;
        }
    }
    
    console.log(cnt);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));