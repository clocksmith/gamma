/* Original candidate for LeetCode 2844. Contract: https://leetcode.com/problems/minimum-operations-to-make-a-special-number/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n) time; O(1) Python, O(n) JS temporary space */
"use strict";
function solve(num){const n=num.length;let ans=n-(num.includes('0')?1:0);for(const end of ['00','25','50','75']){let j=num.lastIndexOf(end[1]);if(j>=0){let i=num.slice(0,j).lastIndexOf(end[0]);if(i>=0)ans=Math.min(ans,n-i-2);}}return ans;}
module.exports = solve;
