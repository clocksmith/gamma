"use strict";
function solve(rectangles){const xs=[...new Set(rectangles.flatMap(r=>[r[0],r[2]]))].sort((a,b)=>a-b);let area=0n;
 for(let i=0;i+1<xs.length;i++){const intervals=rectangles.filter(r=>r[0]<=xs[i]&&xs[i]<r[2]).map(r=>[r[1],r[3]]).sort((a,b)=>a[0]-b[0]);let length=0,end=-1;
  for(const [bottom,top] of intervals){length+=Math.max(0,top-Math.max(bottom,end));end=Math.max(end,top);}area+=BigInt(xs[i+1]-xs[i])*BigInt(length);
 }return Number(area%1000000007n);
}

function rectangleArea(rectangles) { return solve(rectangles); }
module.exports=solve;
module.exports.rectangleArea=rectangleArea;
