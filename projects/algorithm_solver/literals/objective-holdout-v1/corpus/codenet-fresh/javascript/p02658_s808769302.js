"use strict";
const main = arg => {
    var input = arg.split('\n');
    var line = input.shift();
    var lines = input.shift().split(' ').map(i => BigInt(i));

    var answer =  lines[0];

    if(lines.includes(0n)){
        console.log(0);
        return;
    }

    for(let i = 1; i < line;i++){

        answer = answer * lines[i];
        if(answer > 1000000000000000000n){
            console.log(-1);
            return;
        }
    }


    console.log(answer.toString());



}

main(require("fs").readFileSync("/dev/stdin", "utf8"));