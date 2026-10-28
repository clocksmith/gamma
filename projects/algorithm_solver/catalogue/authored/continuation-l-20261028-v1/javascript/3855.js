"use strict";
function solve(l, r, k) {
const modulus=1000000007n;function power(base,exponent){let result=1n;while(exponent>0){if(exponent%2===1)result=result*base%modulus;base=base*base%modulus;exponent=Math.floor(exponent/2);}return result;}const digitSum=BigInt((l+r)*(r-l+1)/2),repunit=(power(10n,k)-1n+modulus)%modulus*111111112n%modulus;return Number(digitSum*power(BigInt(r-l+1),k-1)%modulus*repunit%modulus);
}
function sumOfNumbers(l, r, k) { return solve(l, r, k); }
module.exports=solve;
module.exports.sumOfNumbers=sumOfNumbers;
