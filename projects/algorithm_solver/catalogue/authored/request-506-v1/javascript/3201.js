// Original implementation. Contract: https://leetcode.com/problems/find-the-maximum-length-of-valid-subsequence-i/
"use strict";
function solve(a){const counts=[0,0];let last=-1,alt=0;for(const x of a){const p=x%2;counts[p]++;if(p!==last){alt++;last=p;}}return Math.max(...counts,alt);}
module.exports = solve;
