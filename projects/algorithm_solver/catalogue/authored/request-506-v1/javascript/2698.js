// Original candidate. Contract: https://leetcode.com/problems/find-the-punishment-number-of-an-integer/
"use strict";
function solve(n){let ans=0;for(let x=1;x<=n;x++){const s=String(x*x);function match(i,r){if(i===s.length)return r===0;let v=0;for(let j=i;j<s.length;j++){v=v*10+Number(s[j]);if(v>r)break;if(match(j+1,r-v))return true;}return false;}if(match(0,x))ans+=x*x;}return ans;}
module.exports = solve;
