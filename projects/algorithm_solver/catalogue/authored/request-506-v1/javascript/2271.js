// Original candidate. Contract: https://leetcode.com/problems/maximum-white-tiles-covered-by-a-carpet/
"use strict";
function solve(tiles,L){const a=tiles.map(x=>x.slice()).sort((a,b)=>a[0]-b[0]);let j=0,total=0,ans=0;for(let i=0;i<a.length;i++){const end=a[i][0]+L;while(j<a.length&&a[j][1]<end){total+=a[j][1]-a[j][0]+1;j++;}ans=Math.max(ans,total+(j<a.length?Math.max(0,end-a[j][0]):0));if(j>i)total-=a[i][1]-a[i][0]+1;else j=i+1;}return ans;}
module.exports = solve;
