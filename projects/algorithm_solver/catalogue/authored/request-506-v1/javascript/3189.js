// Original implementation. Contract: https://leetcode.com/problems/minimum-moves-to-get-a-peaceful-board/
"use strict";
function solve(rooks){const x=rooks.map(p=>p[0]).sort((a,b)=>a-b),y=rooks.map(p=>p[1]).sort((a,b)=>a-b);return x.reduce((s,v,i)=>s+Math.abs(v-i)+Math.abs(y[i]-i),0);}
module.exports = solve;
