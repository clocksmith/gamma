// Original implementation. Contract: https://leetcode.com/problems/frog-jump-ii/
"use strict";
function solve(a){let out=a[1]-a[0];for(let i=2;i<a.length;i++)out=Math.max(out,a[i]-a[i-2]);return out;}
module.exports = solve;
