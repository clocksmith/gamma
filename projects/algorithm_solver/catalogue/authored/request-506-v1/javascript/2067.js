// Original candidate implementation. Contract: https://leetcode.com/problems/number-of-equal-count-substrings/
"use strict";
function solve(s,count){let answer=0;const a=[...s].map(c=>c.charCodeAt(0)-97);for(let d=1;d<=26&&d*count<=s.length;d++){const w=d*count,f=Array(26).fill(0);let matched=0;for(let i=0;i<a.length;i++){const c=a[i];matched-=Number(f[c]===count);f[c]++;matched+=Number(f[c]===count);if(i>=w){const old=a[i-w];matched-=Number(f[old]===count);f[old]--;matched+=Number(f[old]===count);}if(i+1>=w&&matched===d)answer++;}}return answer;}
module.exports = solve;
