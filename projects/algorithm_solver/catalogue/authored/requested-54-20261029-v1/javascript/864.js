"use strict";
function solve(grid){const m=grid.length,n=grid[0].length;let start,target=0;
 for(let r=0;r<m;r++)for(let c=0;c<n;c++){const ch=grid[r][c];if(ch==='@')start=[r,c,0,0];else if(ch>='a'&&ch<='f')target|=1<<(ch.charCodeAt(0)-97);}
 const key=(r,c,mask)=>(mask*m+r)*n+c,q=[start],seen=new Set([key(start[0],start[1],0)]);
 for(let h=0;h<q.length;h++){const [r,c,mask,d]=q[h];if(mask===target)return d;
  for(const [a,b] of [[r-1,c],[r+1,c],[r,c-1],[r,c+1]]){if(a<0||a>=m||b<0||b>=n)continue;const ch=grid[a][b];if(ch==='#'||(ch>='A'&&ch<='F'&&!(mask&(1<<(ch.charCodeAt(0)-65)))))continue;
   const next=ch>='a'&&ch<='f'?mask|(1<<(ch.charCodeAt(0)-97)):mask,k=key(a,b,next);if(!seen.has(k)){seen.add(k);q.push([a,b,next,d+1]);}
  }
 }return -1;
}

function shortestPathAllKeys(grid) { return solve(grid); }
module.exports=solve;
module.exports.shortestPathAllKeys=shortestPathAllKeys;
