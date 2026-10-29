"use strict";
function solve(grid) {
 const n=grid.length, labels=Array.from({length:n},()=>Array(n).fill(-1)), sizes=[];
 for(let r=0;r<n;r++) for(let c=0;c<n;c++) {
  if(!grid[r][c] || labels[r][c]>=0) continue;
  const id=sizes.length, stack=[[r,c]]; labels[r][c]=id; let area=0;
  while(stack.length){const [x,y]=stack.pop(); area++;
   for(const [a,b] of [[x-1,y],[x+1,y],[x,y-1],[x,y+1]]) if(a>=0&&a<n&&b>=0&&b<n&&grid[a][b]&&labels[a][b]<0){labels[a][b]=id;stack.push([a,b]);}
  } sizes.push(area);
 }
 let best=0;for(const area of sizes)best=Math.max(best,area);
 for(let r=0;r<n;r++) for(let c=0;c<n;c++) if(!grid[r][c]) {
  const ids=new Set(); for(const [a,b] of [[r-1,c],[r+1,c],[r,c-1],[r,c+1]]) if(a>=0&&a<n&&b>=0&&b<n&&labels[a][b]>=0) ids.add(labels[a][b]);
  let area=1;for(const id of ids)area+=sizes[id];best=Math.max(best,area);
 } return best;
}

function largestIsland(grid) { return solve(grid); }
module.exports=solve;
module.exports.largestIsland=largestIsland;
