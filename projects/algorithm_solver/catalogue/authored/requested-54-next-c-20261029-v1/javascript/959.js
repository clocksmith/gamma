"use strict";
function solve(grid){const n=grid.length,parent=Array.from({length:4*n*n},(_,i)=>i),rank=Array(4*n*n).fill(0);let count=parent.length;
 function find(x){while(parent[x]!==x){parent[x]=parent[parent[x]];x=parent[x];}return x;}
 function union(a,b){a=find(a);b=find(b);if(a===b)return;if(rank[a]<rank[b])[a,b]=[b,a];parent[b]=a;if(rank[a]===rank[b])rank[a]++;count--;}
 for(let r=0;r<n;r++)for(let c=0;c<n;c++){const base=4*(r*n+c);if(grid[r][c]!=='/'){union(base,base+1);union(base+2,base+3);}if(grid[r][c]!=='\\'){union(base,base+3);union(base+1,base+2);}if(r+1<n)union(base+2,base+4*n);if(c+1<n)union(base+1,base+7);}return count;
}

function regionsBySlashes(grid) { return solve(grid); }
module.exports=solve;module.exports.regionsBySlashes=regionsBySlashes;
