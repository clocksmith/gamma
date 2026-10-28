'use strict';
// Separate iterative flood with owned seen bitmap, no caller writes.
function solve(grid){
 const rows=grid.length,cols=grid[0].length,seen=new Uint8Array(rows*cols);let answer=0;
 for(let r=0;r<rows;r++)for(let c=0;c<cols;c++){
  if(grid[r][c]||seen[r*cols+c])continue;
  const stack=[[r,c]];seen[r*cols+c]=1;let closed=true;
  while(stack.length){const [i,j]=stack.pop();if(i===0||j===0||i===rows-1||j===cols-1)closed=false;
   for(const [u,v] of [[i-1,j],[i+1,j],[i,j-1],[i,j+1]])if(u>=0&&u<rows&&v>=0&&v<cols&&!grid[u][v]&&!seen[u*cols+v]){seen[u*cols+v]=1;stack.push([u,v]);}
  }
  if(closed)answer++;
 }
 return answer;
}
const closedIsland=solve;
class Solution{closedIsland(grid){return solve(grid);}}
if(typeof module !== 'undefined')module.exports={solve,Solution,closedIsland};
