/* Original candidate for LeetCode 2865. Contract: https://leetcode.com/problems/beautiful-towers-i/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n^2) time, O(1) space; n <= 1000, sums <= 10^12 */
"use strict";
function solve(heights){let ans=0;for(let p=0;p<heights.length;p++){let total=heights[p],h=heights[p];for(let i=p-1;i>=0;i--){h=Math.min(h,heights[i]);total+=h;}h=heights[p];for(let i=p+1;i<heights.length;i++){h=Math.min(h,heights[i]);total+=h;}ans=Math.max(ans,total);}return ans;}
module.exports = solve;
