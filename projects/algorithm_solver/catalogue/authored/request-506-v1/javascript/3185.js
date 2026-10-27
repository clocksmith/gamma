// Original candidate. Contract: https://leetcode.com/problems/count-pairs-that-form-a-complete-day-ii/
"use strict";
function solve(hours){const c=Array(24).fill(0);let ans=0;for(const x of hours){const r=x%24;ans+=c[(24-r)%24];c[r]++;}return ans;}
module.exports = solve;
