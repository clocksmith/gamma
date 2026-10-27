// Original candidate implementation. Contract: https://leetcode.com/problems/find-the-score-of-all-prefixes-of-an-array/
"use strict";
function solve(nums){const out=[];let mx=0,total=0;for(const x of nums){mx=Math.max(mx,x);total+=mx+x;out.push(total);}return out;}
module.exports = solve;
