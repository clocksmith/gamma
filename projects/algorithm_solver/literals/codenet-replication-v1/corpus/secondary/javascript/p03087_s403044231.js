"use strict";
    
const main = arg => {
    arg = arg.split("\n");
    const N  = parseInt(arg[0].split(" ")[0]);
    const Q  = arg[0].split(" ")[1];
    const S  = arg[1];

    let dp = new Array(N).fill(0);
    let cnt = 0;
    
    for(let i in dp) {
        if(S[i] === "A" && S[parseInt(i)+1] === "C") {
            cnt++;
        }
        
        dp[parseInt(i)+1] = cnt;
    }

    for(let i=0; i<Q; i++) {
        let lr = arg[i+2].split(" ");
        let l = lr[0];
        let r = lr[1];
        
        console.log(dp[r-1]-dp[l-1]);
    }
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));
