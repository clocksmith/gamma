"use strict";
    
const divisor = num => {
    let results = [];
    
    for(let i=1; i<=num; i++) {
        if( (num % i === 0) ) {
            results.push(i);
        }
    }
    
    return results;
}

const getGcd = (a, b) => {
  return a ? getGcd(b % a, a) : b;
}

const main = arg => {
    arg = arg.trim().split("\n");
    const A = parseInt(arg[0].split(" ")[0]);
    const B = parseInt(arg[0].split(" ")[1]);
    
    // 最大公約数を見つける
    let gcd = getGcd(A, B);
    
    let answer = 1;

    // 最大公約数の素因数の数が答えになる
    // ループを回すのは平方根までで良い
    for(let i=2; i*i<=gcd; i++) {
        if(gcd % i === 0) {
            answer++;
            while(gcd%i===0) gcd /= i;
        }
    }
    
    if(gcd !== 1) {
        answer++;
    }
    
    console.log(answer);
}
main(require('fs').readFileSync('/dev/stdin', 'utf8'));
