/* Original candidate for LeetCode 3111. Contract: https://leetcode.com/problems/minimum-rectangles-to-cover-points/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: O(n log n) time, O(n) space */
"use strict";
function solve(points,w){const xs=points.map(p=>p[0]).sort((a,b)=>a-b);let end=-1,ans=0;for(const x of xs)if(x>end){ans++;end=x+w;}return ans;}
module.exports = solve;
