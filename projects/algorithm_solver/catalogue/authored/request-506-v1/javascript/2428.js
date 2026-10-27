/* Original candidate for LeetCode 2428. Contract: https://leetcode.com/problems/maximum-sum-of-an-hourglass/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time, O(1) extra space */
"use strict";
function solve(grid){let ans=0;for(let i=0;i+2<grid.length;i++)for(let j=0;j+2<grid[0].length;j++){let v=grid[i+1][j+1];for(let k=0;k<3;k++)v+=grid[i][j+k]+grid[i+2][j+k];ans=Math.max(ans,v);}return ans;}
module.exports = solve;
