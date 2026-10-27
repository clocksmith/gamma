// Original candidate implementation. Contract: https://leetcode.com/problems/number-of-adjacent-elements-with-the-same-color/
"use strict";
function solve(n,queries){const a=Array(n).fill(0),out=[];let pairs=0;for(const [i,c] of queries){for(const j of [i-1,i+1])if(j>=0&&j<n){if(a[i]!==0&&a[i]===a[j])pairs--;if(c===a[j])pairs++;}a[i]=c;out.push(pairs);}return out;}
module.exports = solve;
