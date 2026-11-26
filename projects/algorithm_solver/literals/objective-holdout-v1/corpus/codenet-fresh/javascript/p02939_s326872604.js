"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const S = arg[0];
    
    let cnt     = 0;
    let before  = "";
    let current = "";
    let debug   = [];
    
    for(let i=0; i<S.length; i++) {
        current += S[i];
        
        if(current === before) {
            continue;
        }
        
        before = current;
        debug.push(current);
        
        current = "";
        
        cnt++;
    }
    
    console.log(debug.length);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));