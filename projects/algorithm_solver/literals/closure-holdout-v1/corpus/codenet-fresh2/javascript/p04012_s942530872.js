"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const w = arg[0].split("");
    
    const set = new Set(w);
    const unique = [...set];
    
    for(let i in unique) {
        if(w.filter(n=>n===unique[i]).length % 2 !== 0) {
            console.log("No");
            return;
        }   
    }
    
    console.log("Yes");
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));