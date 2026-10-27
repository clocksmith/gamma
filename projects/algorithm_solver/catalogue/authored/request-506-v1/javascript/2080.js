/* Original candidate for LeetCode 2080. Contract: https://leetcode.com/problems/range-frequency-queries/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows RangeFreqQuery class-call arrays.
Complexity: O(n) initialization, O(log n) per query, O(n+q) space */
"use strict";
function solve(operations,args){const positions=new Map();args[0][0].forEach((x,i)=>{if(!positions.has(x))positions.set(x,[]);positions.get(x).push(i);});function bound(a,x){let l=0,r=a.length;while(l<r){let m=(l+r)>>1;if(a[m]<x)l=m+1;else r=m;}return l;}return [null,...args.slice(1).map(([l,r,v])=>{let a=positions.get(v)||[];return bound(a,r+1)-bound(a,l);})];}
module.exports = solve;
