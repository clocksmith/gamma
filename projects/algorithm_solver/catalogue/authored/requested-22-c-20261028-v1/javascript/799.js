"use strict";
function solve(poured, query_row, query_glass) {
let row=[poured];for(let r=0;r<query_row;r++){const following=new Array(r+2).fill(0);for(let c=0;c<row.length;c++){if(row[c]>1){const half=(row[c]-1)/2;following[c]+=half;following[c+1]+=half;}}row=following;}return Math.min(1,row[query_glass]);
}
function champagneTower(poured, query_row, query_glass) { return solve(poured, query_row, query_glass); }
module.exports=solve;
module.exports.champagneTower=champagneTower;
