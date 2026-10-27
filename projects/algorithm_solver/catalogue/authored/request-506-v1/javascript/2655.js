// Original candidate implementation. Contract: https://leetcode.com/problems/find-maximal-uncovered-ranges/
"use strict";
function solve(n,ranges){const a=[...ranges].sort((a,b)=>a[0]-b[0]||a[1]-b[1]),out=[];let next=0;for(const [l,r] of a){if(l>next)out.push([next,l-1]);next=Math.max(next,r+1);}if(next<n)out.push([next,n-1]);return out;}
module.exports = solve;
