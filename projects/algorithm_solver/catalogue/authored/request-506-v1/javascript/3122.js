// Original candidate implementation. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-satisfy-conditions/
"use strict";
function solve(grid){let dp=Array(10).fill(0);for(let c=0;c<grid[0].length;c++){const f=Array(10).fill(0);for(const row of grid)f[row[c]]++;const next=Array(10).fill(Infinity);for(let d=0;d<10;d++)for(let p=0;p<10;p++)if(p!==d)next[d]=Math.min(next[d],dp[p]+grid.length-f[d]);dp=next;}return Math.min(...dp);}
module.exports = solve;
