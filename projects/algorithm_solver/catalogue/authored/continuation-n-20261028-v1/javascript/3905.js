"use strict";
function solve(n, m, sources) {
const grid=Array.from({length:n},()=>Array(m).fill(0));let frontier=[];for(const [row,col,color] of sources){grid[row][col]=color;frontier.push(row*m+col);}while(frontier.length){const proposals=new Map();for(const cell of frontier){const row=Math.floor(cell/m),col=cell%m;for(const [a,b] of [[row-1,col],[row+1,col],[row,col-1],[row,col+1]])if(a>=0&&a<n&&b>=0&&b<m&&grid[a][b]===0){const key=a*m+b;proposals.set(key,Math.max(proposals.get(key)||0,grid[row][col]));}}frontier=[...proposals.keys()];for(const [cell,color] of proposals)grid[Math.floor(cell/m)][cell%m]=color;}return grid;
}
function colorGrid(n, m, sources) { return solve(n, m, sources); }
module.exports=solve;
module.exports.colorGrid=colorGrid;
