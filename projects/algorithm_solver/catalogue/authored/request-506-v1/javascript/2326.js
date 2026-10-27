// Original implementation. Contract: https://leetcode.com/problems/spiral-matrix-iv/
"use strict";
function solve(m,n,a){const out=Array.from({length:m},()=>Array(n).fill(-1)),dirs=[[0,1],[1,0],[0,-1],[-1,0]];let r=0,c=0,d=0;for(const x of a){out[r][c]=x;let nr=r+dirs[d][0],nc=c+dirs[d][1];if(nr<0||nr>=m||nc<0||nc>=n||out[nr][nc]!==-1){d=(d+1)%4;nr=r+dirs[d][0];nc=c+dirs[d][1];}r=nr;c=nc;}return out;}
module.exports = solve;
