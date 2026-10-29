"use strict";
function solve(grid) {
const n=grid.length;let best=Array.from({length:n},()=>new Int32Array(n).fill(-1));best[0][0]=grid[0][0];for(let step=1;step<2*n-1;step++){const current=Array.from({length:n},()=>new Int32Array(n).fill(-1)),first=Math.max(0,step-n+1),last=Math.min(n-1,step);for(let row1=first;row1<=last;row1++){const cell1=grid[row1][step-row1];if(cell1===-1)continue;for(let row2=row1;row2<=last;row2++){const cell2=grid[row2][step-row2];if(cell2===-1)continue;let previous=best[row1][row2];if(row1&&best[row1-1][row2]>previous)previous=best[row1-1][row2];if(row2>row1&&best[row1][row2-1]>previous)previous=best[row1][row2-1];if(row1&&best[row1-1][row2-1]>previous)previous=best[row1-1][row2-1];if(previous===-1)continue;current[row1][row2]=previous+cell1+(row2!==row1?cell2:0);}}best=current;}return Math.max(0,best[n-1][n-1]);
}
function cherryPickup(grid) { return solve(grid); }
module.exports=solve;
module.exports.cherryPickup=cherryPickup;
