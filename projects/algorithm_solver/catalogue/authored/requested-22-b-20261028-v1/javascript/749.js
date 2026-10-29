"use strict";
function solve(isInfected) {
const grid=isInfected.map(row=>row.slice()),rows=grid.length,cols=grid[0].length;let total=0;for(;;){const seen=grid.map(row=>row.map(()=>false)),regions=[];for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){if(grid[r][c]!==1||seen[r][c])continue;seen[r][c]=true;const cells=[],threatened=new Set(),stack=[[r,c]];let walls=0;while(stack.length){const [x,y]=stack.pop();cells.push([x,y]);for(const [u,v] of [[x-1,y],[x+1,y],[x,y-1],[x,y+1]]){if(u<0||u>=rows||v<0||v>=cols)continue;if(grid[u][v]===0){threatened.add(u*cols+v);walls++;}else if(grid[u][v]===1&&!seen[u][v]){seen[u][v]=true;stack.push([u,v]);}}}regions.push([cells,threatened,walls]);}if(!regions.length)return total;let best=0;for(let i=1;i<regions.length;i++)if(regions[i][1].size>regions[best][1].size)best=i;if(!regions[best][1].size)return total;total+=regions[best][2];for(const [x,y] of regions[best][0])grid[x][y]=2;regions.forEach(([,threatened],i)=>{if(i!==best)for(const cell of threatened)grid[Math.floor(cell/cols)][cell%cols]=1;});}
}
function containVirus(isInfected) { return solve(isInfected); }
module.exports=solve;
module.exports.containVirus=containVirus;
