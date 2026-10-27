// Original candidate. Contract: https://leetcode.com/problems/minimize-maximum-value-in-a-grid/
"use strict";
function solve(grid){const m=grid.length,n=grid[0].length,rows=Array(m).fill(0),cols=Array(n).fill(0),out=Array.from({length:m},()=>Array(n).fill(0)),cells=[];for(let i=0;i<m;i++)for(let j=0;j<n;j++)cells.push([grid[i][j],i,j]);cells.sort((a,b)=>a[0]-b[0]);for(const[v,i,j]of cells){const x=Math.max(rows[i],cols[j])+1;out[i][j]=rows[i]=cols[j]=x;}return out;}
module.exports = solve;
