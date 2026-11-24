"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const S = arg[0].split("");
    const list = [];
    
    let last;
    
    for(let i in S) {
        if(S[i] !== last) {
            list.push(S[i]);
        }
        
        last = S[i];
    }

    console.log(list.join("").length - 1);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));