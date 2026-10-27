// Original candidate. Contract: https://leetcode.com/problems/maximum-points-inside-the-square/
"use strict";
function solve(points,s){const near=new Map();let limit=Infinity;for(let i=0;i<points.length;i++){const[x,y]=points[i],d=Math.max(Math.abs(x),Math.abs(y)),tag=s[i];if(near.has(tag)){limit=Math.min(limit,Math.max(d,near.get(tag)));near.set(tag,Math.min(d,near.get(tag)));}else near.set(tag,d);}let ans=0;for(const d of near.values())if(d<limit)ans++;return ans;}
module.exports = solve;
