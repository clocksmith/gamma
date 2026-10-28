"use strict";
function solve(n, k) {
const choose=Array.from({length:51},()=>Array(51).fill(0));for(let i=0;i<=50;i++){choose[i][0]=1;for(let j=1;j<=i;j++)choose[i][j]=(i?choose[i-1][j-1]:0)+(i?choose[i-1][j]:0);}let answer=0,remaining=k;for(let bit=49;bit>=0;bit--){const zeroCount=remaining>=0&&remaining<=bit?choose[bit][remaining]:0;if(n>zeroCount){answer+=2**bit;n-=zeroCount;remaining--;}}return answer;
}
function nthSmallest(n, k) { return solve(n, k); }
module.exports=solve;
module.exports.nthSmallest=nthSmallest;
