// Original implementation. Contract: https://leetcode.com/problems/minimum-length-of-anagram-concatenation/
"use strict";
function solve(s){const n=s.length;for(let size=1;size<=n;size++){if(n%size)continue;const base=Array(26).fill(0);for(let j=0;j<size;j++)base[s.charCodeAt(j)-97]++;let good=true;for(let i=size;i<n&&good;i+=size){const c=Array(26).fill(0);for(let j=i;j<i+size;j++)c[s.charCodeAt(j)-97]++;good=c.every((x,j)=>x===base[j]);}if(good)return size;}}
module.exports = solve;
