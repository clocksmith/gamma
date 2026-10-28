'use strict';
// Separate immutable-grid variant, using at most 25 visited bits.
function solve(grid) {
  const cells = [], indices = new Map();
  for (let r=0;r<grid.length;r++) for (let c=0;c<grid[r].length;c++) if(grid[r][c]) {indices.set(`${r},${c}`,cells.length);cells.push([r,c]);}
  const weights=cells.map(([r,c])=>grid[r][c]);
  const neighbors=cells.map(([r,c])=>[[r-1,c],[r+1,c],[r,c-1],[r,c+1]].map(([i,j])=>indices.get(`${i},${j}`)).filter(v=>v!==undefined));
  const upper=weights.reduce((a,b)=>a+b,0);let best=0;
  function visit(last,mask,total) {
    best=Math.max(best,total);if(best===upper)return;
    for(const next of neighbors[last])if((mask & (1<<next))===0){visit(next,mask|(1<<next),total+weights[next]);if(best===upper)return;}
  }
  for(let i=0;i<weights.length;i++){visit(i,1<<i,weights[i]);if(best===upper)break;}
  return best;
}
const getMaximumGold=solve;
class Solution{getMaximumGold(grid){return solve(grid);}}
if(typeof module !== 'undefined')module.exports={solve,Solution,getMaximumGold};
