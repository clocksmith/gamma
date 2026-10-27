// Original candidate. Contract: https://leetcode.com/problems/sum-of-matrix-after-queries/
"use strict";
function solve(n,queries){const seen=[new Set(),new Set()];let ans=0;for(let i=queries.length-1;i>=0;i--){const[t,j,v]=queries[i];if(!seen[t].has(j)){ans+=(n-seen[1-t].size)*v;seen[t].add(j);}}return ans;}
module.exports = solve;
