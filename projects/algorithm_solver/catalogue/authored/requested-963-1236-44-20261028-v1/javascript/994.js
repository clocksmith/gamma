"use strict";
function solve(grid){const rows=grid.length,cols=grid[0].length,q=[],seen=new Set();let fresh=0,answer=0;for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){if(grid[r][c]===2){q.push([r,c,0]);seen.add(r*cols+c);}else if(grid[r][c]===1)fresh++;}for(let at=0;at<q.length;at++){const [r,c,t]=q[at];answer=Math.max(answer,t);for(const [nr,nc]of [[r-1,c],[r+1,c],[r,c-1],[r,c+1]])if(nr>=0&&nr<rows&&nc>=0&&nc<cols&&grid[nr][nc]===1&&!seen.has(nr*cols+nc)){seen.add(nr*cols+nc);fresh--;q.push([nr,nc,t+1]);}}return fresh?-1:answer;}

function orangesRotting(grid){return solve(grid);}
module.exports=solve;
module.exports.orangesRotting=orangesRotting;
