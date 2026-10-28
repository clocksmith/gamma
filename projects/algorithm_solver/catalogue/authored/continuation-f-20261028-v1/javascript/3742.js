"use strict";
function solve(grid, k) {
const width=grid[0].length,budget=Math.min(k,grid.length+width-2);let previous=Array.from({length:width},()=>new Int32Array(budget+1).fill(-1));for(let i=0;i<grid.length;i++){const current=Array.from({length:width},()=>new Int32Array(budget+1).fill(-1));for(let j=0;j<width;j++){const value=grid[i][j],cost=value!==0?1:0;if(i===0&&j===0){current[j][0]=0;continue;}for(let spent=cost;spent<=budget;spent++){const best=Math.max(i?previous[j][spent-cost]:-1,j?current[j-1][spent-cost]:-1);if(best>=0)current[j][spent]=best+value;}}previous=current;}let answer=-1;for(const value of previous[width-1])answer=Math.max(answer,value);return answer;
}
function maxPathScore(grid, k) { return solve(grid, k); }
module.exports=solve;
module.exports.maxPathScore=maxPathScore;
