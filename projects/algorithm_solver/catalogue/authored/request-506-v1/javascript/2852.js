// Original implementation. Contract: https://leetcode.com/problems/sum-of-remoteness-of-all-cells/
"use strict";
function solve(grid){const n=grid.length,seen=new Uint8Array(n*n);let total=0,answer=0;for(const row of grid)for(const x of row)if(x!==-1)total+=x;for(let r=0;r<n;r++)for(let c=0;c<n;c++){const start=r*n+c;if(grid[r][c]===-1||seen[start])continue;const q=[start];seen[start]=1;let amount=0;for(let h=0;h<q.length;h++){const x=Math.floor(q[h]/n),y=q[h]%n;amount+=grid[x][y];for(const [a,b] of [[x-1,y],[x+1,y],[x,y-1],[x,y+1]])if(a>=0&&a<n&&b>=0&&b<n&&grid[a][b]!==-1&&!seen[a*n+b]){seen[a*n+b]=1;q.push(a*n+b);}}answer+=q.length*(total-amount);}return answer;}
module.exports = solve;
