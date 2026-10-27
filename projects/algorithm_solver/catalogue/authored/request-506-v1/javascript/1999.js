// Original candidate implementation. Contract: https://leetcode.com/problems/smallest-greater-multiple-made-of-two-digits/
"use strict";
function solve(k,digit1,digit2){const digits=[...new Set([digit1,digit2])].sort((a,b)=>a-b),queue=digits.filter(Boolean);for(let h=0;h<queue.length;h++){const v=queue[h];if(v>k&&v%k===0)return v;for(const d of digits){const next=v*10+d;if(next<=2147483647)queue.push(next);}}return -1;}
module.exports = solve;
