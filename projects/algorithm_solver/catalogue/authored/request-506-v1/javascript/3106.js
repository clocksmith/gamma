// Original implementation. Contract: https://leetcode.com/problems/lexicographically-smallest-string-after-operations-with-constraint/
"use strict";
function solve(s,k){let out='';for(const c of s){const x=c.charCodeAt(0)-97,cost=Math.min(x,26-x);if(cost<=k){out+='a';k-=cost;}else{out+=String.fromCharCode(97+x-k);k=0;}}return out;}
module.exports = solve;
