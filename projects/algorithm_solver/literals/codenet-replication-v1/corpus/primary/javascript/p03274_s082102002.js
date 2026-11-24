"use strict";
    
const main = arg => {
    arg = arg.split("\n");
    const N = parseInt(arg[0].split(" ")[0]);
    const K = parseInt(arg[0].split(" ")[1]);
    
    const x = arg[1].split(" ").map(n=>parseInt(n));
    
    const list = [];
    
    for(let i=0; i<=N - K; i++) {
        let left  = x[i];
        let right = x[~~i + K - 1];
        
        // 左側から先にいく or 右側しかいかないパターン
        if(Math.abs(left) < Math.abs(right)) {
            list.push(Math.abs(left) + Math.abs(right - left));
        
        // 右側から先にいく or 左側しかいかないパターン
        } else {
            list.push(Math.abs(right) + Math.abs(right - left));
        }
        
        // console.log(list);
    }
    
    console.log(Math.min(...list));
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));
