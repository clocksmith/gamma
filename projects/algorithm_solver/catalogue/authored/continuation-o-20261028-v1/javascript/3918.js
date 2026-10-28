"use strict";
function solve(n) {
const reversed=Number(String(n).split('').reverse().join('')),left=Math.min(n,reversed),right=Math.max(n,reversed),prime=new Uint8Array(right+1).fill(1);prime[0]=0;if(right>=1)prime[1]=0;for(let v=2;v*v<=right;v++)if(prime[v])for(let x=v*v;x<=right;x+=v)prime[x]=0;let answer=0;for(let v=left;v<=right;v++)if(prime[v])answer+=v;return answer;
}
function sumOfPrimesInRange(n) { return solve(n); }
module.exports=solve;
module.exports.sumOfPrimesInRange=sumOfPrimesInRange;
