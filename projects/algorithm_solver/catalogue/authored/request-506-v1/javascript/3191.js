// Original candidate implementation. Contract: https://leetcode.com/problems/minimum-operations-to-make-binary-array-elements-equal-to-one-i/
"use strict";
function solve(nums){const a=[...nums];let answer=0;for(let i=0;i+2<a.length;i++)if(a[i]===0){answer++;for(let j=i;j<i+3;j++)a[j]^=1;}return a.every(Boolean)?answer:-1;}
module.exports = solve;
