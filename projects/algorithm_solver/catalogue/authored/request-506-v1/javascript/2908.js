// Original candidate. Contract: https://leetcode.com/problems/minimum-sum-of-mountain-triplets-i/
"use strict";
function solve(a){let ans=Infinity;for(let j=1;j<a.length-1;j++){let l=Infinity,r=Infinity;for(let i=0;i<j;i++)l=Math.min(l,a[i]);for(let k=j+1;k<a.length;k++)r=Math.min(r,a[k]);if(l<a[j]&&r<a[j])ans=Math.min(ans,l+a[j]+r);}return ans===Infinity?-1:ans;}
module.exports = solve;
