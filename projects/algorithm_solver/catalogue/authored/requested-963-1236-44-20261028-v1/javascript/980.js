"use strict";
function solve(grid){const cells=[],index=new Map();for(let r=0;r<grid.length;r++)for(let c=0;c<grid[0].length;c++)if(grid[r][c]!==-1){index.set(r+','+c,cells.length);cells.push([r,c]);}let start,end;const adj=cells.map(([r,c],i)=>{if(grid[r][c]===1)start=i;if(grid[r][c]===2)end=i;return [[r-1,c],[r+1,c],[r,c-1],[r,c+1]].filter(p=>index.has(p.join(','))).map(p=>index.get(p.join(',')));}),full=2**cells.length-1,memo=new Map();function count(at,mask){if(at===end)return Number(mask===full);const key=mask*cells.length+at;if(memo.has(key))return memo.get(key);let answer=0;for(const j of adj[at])if(!(mask&(1<<j)))answer+=count(j,mask|(1<<j));memo.set(key,answer);return answer;}return count(start,1<<start);}

function uniquePathsIII(grid){return solve(grid);}
module.exports=solve;
module.exports.uniquePathsIII=uniquePathsIII;
