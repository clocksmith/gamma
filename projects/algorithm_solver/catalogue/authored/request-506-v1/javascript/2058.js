// Original implementation. Contract: https://leetcode.com/problems/find-the-minimum-and-maximum-number-of-nodes-between-critical-points/
"use strict";
function solve(a){const p=[];for(let i=1;i+1<a.length;i++)if((a[i]>a[i-1]&&a[i]>a[i+1])||(a[i]<a[i-1]&&a[i]<a[i+1]))p.push(i);if(p.length<2)return [-1,-1];let best=Infinity;for(let i=1;i<p.length;i++)best=Math.min(best,p[i]-p[i-1]);return [best,p.at(-1)-p[0]];}
module.exports = solve;
