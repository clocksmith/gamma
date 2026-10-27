/* Original candidate for LeetCode 3128. Contract: https://leetcode.com/problems/right-triangles/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time, O(m+n) space; answer < 10^12 */
"use strict";
function solve(grid){let rows=grid.map(r=>r.reduce((a,b)=>a+b,0)),cols=Array(grid[0].length).fill(0);for(const row of grid)for(let j=0;j<row.length;j++)cols[j]+=row[j];let ans=0;for(let i=0;i<grid.length;i++)for(let j=0;j<cols.length;j++)if(grid[i][j])ans+=(rows[i]-1)*(cols[j]-1);return ans;}
module.exports = solve;
