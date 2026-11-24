"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const N = parseInt(arg[0].split(" ")[0]);
    const M = parseInt(arg[0].split(" ")[1]);
    
    const ab = arg.slice(1, M + 1).map(n=>n.split(" ").map(l=>parseInt(l)));
    
    // 区間の終端でソート
    ab.sort((a,b)=>a[1] - b[1]);
    
    let answer = 0;
    let endTime = 0;
    
    // 貪欲
    for(let i=0; i<M; i++) {
        if(ab[i][0] >= endTime) {
            endTime = ab[i][1];
            answer++;
        }
    }
    
    console.log(answer);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));