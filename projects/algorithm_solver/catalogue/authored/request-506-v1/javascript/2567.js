// Original implementation. Contract: https://leetcode.com/problems/minimum-score-by-changing-two-elements/
"use strict";
function solve(nums){const a=[...nums].sort((a,b)=>a-b),n=a.length;return Math.min(a[n-1]-a[2],a[n-2]-a[1],a[n-3]-a[0]);}
module.exports = solve;
