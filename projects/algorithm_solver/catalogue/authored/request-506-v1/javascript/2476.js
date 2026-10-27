// Original candidate. Contract: https://leetcode.com/problems/closest-nodes-queries-in-a-binary-search-tree/
"use strict";
function solve(root,queries){const a=root.filter(x=>x!==null).sort((x,y)=>x-y);return queries.map(x=>{let l=0,r=a.length;while(l<r){let m=(l+r)>>1;if(a[m]<x)l=m+1;else r=m;}return l<a.length&&a[l]===x?[x,x]:[l?a[l-1]:-1,l<a.length?a[l]:-1];});}
module.exports = solve;
