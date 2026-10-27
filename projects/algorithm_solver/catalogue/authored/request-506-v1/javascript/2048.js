// Original implementation. Contract: https://leetcode.com/problems/next-greater-numerically-balanced-number/
"use strict";
function solve(n){for(let x=n+1;;x++){let y=x,c=Array(10).fill(0);while(y){c[y%10]++;y=Math.floor(y/10);}if(c[0]===0&&c.every((v,i)=>v===0||v===i))return x;}}
module.exports = solve;
