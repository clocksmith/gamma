// Original implementation. Contract: https://leetcode.com/problems/finding-the-number-of-visible-mountains/
"use strict";
function solve(peaks){const a=peaks.map(([x,y])=>[x-y,x+y]).sort((a,b)=>a[0]-b[0]||b[1]-a[1]);let end=-Infinity,out=0;for(let i=0;i<a.length;){let j=i+1;while(j<a.length&&a[j][0]===a[i][0]&&a[j][1]===a[i][1])j++;if(a[i][1]>end){out+=j===i+1;end=a[i][1];}i=j;}return out;}
module.exports = solve;
