function solve(grid,k){
 const m=grid.length,n=grid[0].length,size=m*n,value=i=>grid[Math.floor(i/n)][i%n],cells=Array.from({length:size},(_,i)=>i).sort((a,b)=>value(b)-value(a));
 let dist=Array(size).fill(Infinity);dist[0]=0;
 for(let used=0;used<=k;used++){
  if(used){const previous=dist;dist=previous.slice();let best=Infinity,start=0;while(start<size){let end=start;const v=value(cells[start]);while(end<size&&value(cells[end])===v){best=Math.min(best,previous[cells[end]]);end++;}for(let p=start;p<end;p++)dist[cells[p]]=Math.min(dist[cells[p]],best);start=end;}}
  for(let i=0;i<m;i++)for(let j=0;j<n;j++){const p=i*n+j;if(i)dist[p]=Math.min(dist[p],dist[p-n]+grid[i][j]);if(j)dist[p]=Math.min(dist[p],dist[p-1]+grid[i][j]);}
 }
 return dist[size-1];
}

var minCost = solve;
module.exports = solve;
