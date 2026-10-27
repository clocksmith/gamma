// Original candidate. Contract: https://leetcode.com/problems/apply-operations-to-make-two-strings-equal/
"use strict";
function solve(s1,s2,x){const p=[];for(let i=0;i<s1.length;i++)if(s1[i]!==s2[i])p.push(i);if(p.length%2)return -1;const d=Array(p.length+1).fill(0);for(let i=1;i<d.length;i++){d[i]=d[i-1]+x;if(i>=2)d[i]=Math.min(d[i],d[i-2]+2*(p[i-1]-p[i-2]));}return d[p.length]/2;}
module.exports = solve;
