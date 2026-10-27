/* Original candidate for LeetCode 3169. Contract: https://leetcode.com/problems/count-days-without-meetings/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space */
"use strict";
function solve(days,meetings){let end=0,busy=0;for(const [l,r] of [...meetings].sort((a,b)=>a[0]-b[0]))if(r>end){busy+=r-Math.max(end,l-1);end=r;}return days-busy;}
module.exports = solve;
