/* Original candidate for LeetCode 3070. Contract: https://leetcode.com/problems/count-submatrices-with-top-left-element-and-sum-less-than-k/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(mn) time, O(n) space; inclusive <= k despite title */
"use strict";
function solve(grid,k){let sums=Array(grid[0].length).fill(0),ans=0;for(const row of grid){let prefix=0;for(let j=0;j<row.length;j++){prefix+=row[j];sums[j]+=prefix;if(sums[j]<=k)ans++;}}return ans;}
module.exports = solve;
