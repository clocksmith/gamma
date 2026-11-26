"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const S = arg[0].split("");
    
    let flagC = false;
    
    for(let i in S) {
        if(S[i] === "C") flagC = true;
        if(S[i] === "F" && flagC) {
            console.log("Yes");
            return;
        }
    }
    
    console.log("No");
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));