// Original candidate. Contract: https://leetcode.com/problems/find-the-minimum-area-to-cover-all-ones-i/
"use strict";
function solve(grid){let top=grid.length,left=grid[0].length,bottom=-1,right=-1;for(let i=0;i<grid.length;i++)for(let j=0;j<grid[i].length;j++)if(grid[i][j]){top=Math.min(top,i);bottom=Math.max(bottom,i);left=Math.min(left,j);right=Math.max(right,j);}return (bottom-top+1)*(right-left+1);}
module.exports = solve;
