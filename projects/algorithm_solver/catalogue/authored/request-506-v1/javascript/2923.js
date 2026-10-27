// Original candidate. Contract: https://leetcode.com/problems/find-champion-i/
"use strict";
function solve(grid){let c=0;for(let i=1;i<grid.length;i++)if(grid[i][c])c=i;return c;}
module.exports = solve;
