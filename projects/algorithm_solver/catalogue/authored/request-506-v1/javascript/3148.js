/* Original candidate for LeetCode 3148. Contract: https://leetcode.com/problems/maximum-difference-score-in-a-grid/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time, O(n) space; at least one move required */
"use strict";
function solve(grid){let mins=Array(grid[0].length).fill(Infinity),ans=-Infinity;for(const row of grid){let left=Infinity;for(let j=0;j<row.length;j++){let x=row[j],before=Math.min(left,mins[j]);ans=Math.max(ans,x-before);mins[j]=left=Math.min(before,x);}}return ans;}
module.exports = solve;
