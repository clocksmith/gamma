// Original candidate. Contract: https://leetcode.com/problems/longest-non-decreasing-subarray-from-two-arrays/
"use strict";
function solve(A,B){let a=1,b=1,ans=1;for(let i=1;i<A.length;i++){let x=1,y=1;if(A[i]>=A[i-1])x=Math.max(x,a+1);if(A[i]>=B[i-1])x=Math.max(x,b+1);if(B[i]>=A[i-1])y=Math.max(y,a+1);if(B[i]>=B[i-1])y=Math.max(y,b+1);a=x;b=y;ans=Math.max(ans,a,b);}return ans;}
module.exports = solve;
