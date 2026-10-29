"use strict";
function solve(grid, hits) {
const m=grid.length,n=grid[0].length,roof=m*n,cells=new Uint8Array(roof);for(let r=0;r<m;r++)for(let c=0;c<n;c++)cells[r*n+c]=grid[r][c];for(const [r,c] of hits)cells[r*n+c]=0;const parent=new Int32Array(roof+1),size=new Int32Array(roof+1).fill(1);for(let i=0;i<=roof;i++)parent[i]=i;function find(x){let root=x;while(parent[root]!==root)root=parent[root];while(parent[x]!==root){const next=parent[x];parent[x]=root;x=next;}return root;}function union(a,b){a=find(a);b=find(b);if(a===b)return;if(size[a]<size[b]){const t=a;a=b;b=t;}parent[b]=a;size[a]+=size[b];}function attach(r,c){const index=r*n+c;if(r===0)union(index,roof);if(r+1<m&&cells[index+n])union(index,index+n);if(r>0&&cells[index-n])union(index,index-n);if(c+1<n&&cells[index+1])union(index,index+1);if(c>0&&cells[index-1])union(index,index-1);}for(let r=0;r<m;r++)for(let c=0;c<n;c++)if(cells[r*n+c])attach(r,c);const answer=new Array(hits.length).fill(0);for(let k=hits.length-1;k>=0;k--){const [r,c]=hits[k];if(!grid[r][c])continue;const before=size[find(roof)];cells[r*n+c]=1;attach(r,c);answer[k]=Math.max(0,size[find(roof)]-before-1);}return answer;
}
function hitBricks(grid, hits) { return solve(grid, hits); }
module.exports=solve;
module.exports.hitBricks=hitBricks;
