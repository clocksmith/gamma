// Original implementation. Contract: https://leetcode.com/problems/special-array-ii/
"use strict";
function solve(a,queries){const bad=Array(a.length).fill(0);for(let i=1;i<a.length;i++)bad[i]=bad[i-1]+(a[i]%2===a[i-1]%2);return queries.map(([l,r])=>bad[l]===bad[r]);}
module.exports = solve;
