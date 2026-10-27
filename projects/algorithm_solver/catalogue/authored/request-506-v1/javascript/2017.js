/* Original candidate for LeetCode 2017. Contract: https://leetcode.com/problems/grid-game/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time, O(1) space */
"use strict";
function solve(grid) {
 let top=grid[0].reduce((a,b)=>a+b,0),bottom=0,best=Infinity;
 for(let i=0;i<grid[0].length;i++){top-=grid[0][i];best=Math.min(best,Math.max(top,bottom));bottom+=grid[1][i];}
 return best;
}
module.exports = solve;
