// Original candidate. Contract: https://leetcode.com/problems/maximum-xor-product/
"use strict";
function solve(a,b,n){a=BigInt(a);b=BigInt(b);const mask=(1n<<BigInt(n))-1n;let u=a&~mask,v=b&~mask;for(let i=n-1;i>=0;i--){const bit=1n<<BigInt(i);if((a&bit)===(b&bit)){u|=bit;v|=bit;}else if(u<v)u|=bit;else v|=bit;}return Number(u*v%1000000007n);}
module.exports = solve;
