"use strict";
    
const main = arg => {
    arg = arg.trim().split("\n");
    const S = arg[0].split("");
    
    let answer = "-1 -1";
    
    for(let i=0; i<S.length-1; i++) {
        let next = S[parseInt(i) + 1];
        let nextNext = S[parseInt(i) + 2];
         
        // XX が存在すればそれが答え
        if(S[i] === next) {
            answer = (parseInt(i) + 1) + " " +  (parseInt(i) + 2);
            break;
        }
        
        // XYXが存在すればそれが答え
        if(S[i] === nextNext) {
            answer = (parseInt(i) + 1) + " " +  (parseInt(i) + 3);
            break;
        }
    }
    
    console.log(answer);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));