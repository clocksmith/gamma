"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const H = parseInt(arg[0].split(" ")[0]);
    const W = parseInt(arg[0].split(" ")[1]);
    
    const N = parseInt(arg[1]);
    const A = arg[2].split(" ").map(n=>parseInt(n));
    
    let temp = [];
    
    if(H * W === 1) {
        console.log(1);
        return;
    }
    
    for(let i=1; i<=N; i++) {
        for(let j=0; j<A[i-1]; j++) {
            temp.push(i);
        }
    }

    let answer = [];
    let list = [];
    let currentH = 0;

    for(let i=0; i<temp.length; i++) {
        list.push(temp[i]);
        
        if(i !== 0 && (parseInt(i) + 1) % W === 0) {
            if(currentH % 2 !== 0) list.reverse()

            answer.push(list.join(" "));
            list = [];
            currentH++;
        }
    }
    
    console.log(answer.join("\n"));
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));