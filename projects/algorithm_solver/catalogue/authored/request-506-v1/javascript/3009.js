// Original candidate. Contract: https://leetcode.com/problems/maximum-number-of-intersections-on-the-chart/
"use strict";
function solve(y){const e=new Map();function add(a,b){e.set(a,(e.get(a)||0)+1);e.set(b+1,(e.get(b+1)||0)-1);}for(let i=1;i<y.length;i++){const a=y[i-1],b=y[i];if(a<b)add(2*a,2*b-1);else add(2*b+1,2*a);}add(2*y[y.length-1],2*y[y.length-1]);let x=0,r=0;for(const k of [...e.keys()].sort((a,b)=>a-b)){x+=e.get(k);r=Math.max(r,x);}return r;}
module.exports = solve;
