// Original candidate. Contract: https://leetcode.com/problems/sum-of-number-and-its-reverse/
"use strict";
function solve(num){for(let x=0;x<=num;x++)if(x+Number(String(x).split('').reverse().join(''))===num)return true;return false;}
module.exports = solve;
