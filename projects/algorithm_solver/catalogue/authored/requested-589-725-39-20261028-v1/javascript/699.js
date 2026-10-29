"use strict";
function solve(positions){const placed=[],out=[];let high=0;for(const [left,size]of positions){const right=left+size;let base=0;for(const [a,b,top]of placed)if(a<right&&left<b)base=Math.max(base,top);const top=base+size;placed.push([left,right,top]);high=Math.max(high,top);out.push(high);}return out;}

function fallingSquares(positions){return solve(positions);}
module.exports=solve;
module.exports.fallingSquares=fallingSquares;
