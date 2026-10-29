"use strict";
function solve(n,restrictions){const rows=restrictions.map(r=>r.slice()).concat([[1,0]]).sort((a,b)=>a[0]-b[0]);for(let i=1;i<rows.length;i++)rows[i][1]=Math.min(rows[i][1],rows[i-1][1]+rows[i][0]-rows[i-1][0]);for(let i=rows.length-2;i>=0;i--)rows[i][1]=Math.min(rows[i][1],rows[i+1][1]+rows[i+1][0]-rows[i][0]);let best=rows[rows.length-1][1]+n-rows[rows.length-1][0];for(let i=1;i<rows.length;i++)best=Math.max(best,Math.floor((rows[i-1][1]+rows[i][1]+rows[i][0]-rows[i-1][0])/2));return best;}

function maxBuilding(n, restrictions){return solve(n, restrictions);}
module.exports=solve;
module.exports.maxBuilding=maxBuilding;
