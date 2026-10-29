"use strict";
function solve(forest){const rows=forest.length,cols=forest[0].length,trees=[];for(let r=0;r<rows;r++)for(let c=0;c<cols;c++)if(forest[r][c]>1)trees.push([forest[r][c],r,c]);trees.sort((a,b)=>a[0]-b[0]);function distance(sr,sc,tr,tc){if(!forest[sr][sc])return -1;const q=[[sr,sc,0]],seen=new Uint8Array(rows*cols);seen[sr*cols+sc]=1;for(let at=0;at<q.length;at++){const [r,c,d]=q[at];if(r===tr&&c===tc)return d;for(const [nr,nc]of [[r-1,c],[r+1,c],[r,c-1],[r,c+1]])if(nr>=0&&nr<rows&&nc>=0&&nc<cols&&forest[nr][nc]&&!seen[nr*cols+nc]){seen[nr*cols+nc]=1;q.push([nr,nc,d+1]);}}return -1;}let r=0,c=0,total=0;for(const [,nr,nc]of trees){const d=distance(r,c,nr,nc);if(d<0)return -1;total+=d;r=nr;c=nc;}return total;}

function cutOffTree(forest){return solve(forest);}
module.exports=solve;
module.exports.cutOffTree=cutOffTree;
