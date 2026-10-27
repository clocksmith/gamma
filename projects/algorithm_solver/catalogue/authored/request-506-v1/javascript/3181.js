// Original implementation. Contract: https://leetcode.com/problems/maximum-total-reward-using-operations-ii/
"use strict";
function solve(a){let bits=1n;for(const x of [...new Set(a)].sort((x,y)=>x-y)){const b=BigInt(x);bits|=(bits&((1n<<b)-1n))<<b;}return bits.toString(2).length-1;}
module.exports = solve;
