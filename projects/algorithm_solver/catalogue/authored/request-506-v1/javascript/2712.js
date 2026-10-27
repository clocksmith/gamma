// Original implementation. Contract: https://leetcode.com/problems/minimum-cost-to-make-all-characters-equal/
"use strict";
function solve(s){let out=0;for(let i=1;i<s.length;i++)if(s[i]!==s[i-1])out+=Math.min(i,s.length-i);return out;}
module.exports = solve;
