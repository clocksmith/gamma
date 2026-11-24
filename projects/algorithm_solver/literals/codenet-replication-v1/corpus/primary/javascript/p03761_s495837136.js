"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const N = parseInt(arg[0]);
    const S = arg.slice(1, N + 1);
    
    const alphabets = "abcdefghijklmnopqrstuvwxyz".split("");
    
    let answer = [];
    
    for(let i in alphabets) {
        let contains = Infinity;
        
        for(let j in S) {
            let cnt = S[j].split("").filter(n=>n===alphabets[i]).length;
            
            if(cnt > 0) {
                contains = Math.min(cnt, contains);
            } else {
                contains = 0;
                break;
            }
        }
        
        for(let j=0; j<contains; j++) {
            answer.push(alphabets[i]);   
        }
    }
    
    console.log(answer.join(""));
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));
