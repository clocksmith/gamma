"use strict";
function solve(barcodes){const counts=new Map();for(const v of barcodes)counts.set(v,(counts.get(v)||0)+1);const out=new Array(barcodes.length);let pos=0;for(const [v,n]of [...counts].sort((a,b)=>b[1]-a[1]||a[0]-b[0]))for(let i=0;i<n;i++){if(pos>=out.length)pos=1;out[pos]=v;pos+=2;}return out;}

function rearrangeBarcodes(barcodes){return solve(barcodes);}
module.exports=solve;
module.exports.rearrangeBarcodes=rearrangeBarcodes;
