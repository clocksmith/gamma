class MinHeap {
  constructor(){this.a=[];}
  push(item){const a=this.a;a.push(item);let i=a.length-1;while(i){const p=(i-1)>>1;if(a[p][0]<=item[0])break;a[i]=a[p];i=p;}a[i]=item;}
  pop(){const a=this.a,first=a[0],last=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let c=2*i+1;if(c+1<a.length&&a[c+1][0]<a[c][0])c++;if(a[c][0]>=last[0])break;a[i]=a[c];i=c;}a[i]=last;}return first;}
}
function solve(n, edges){
 const graph=Array.from({length:n},()=>[]);for(const [u,v,w] of edges){graph[u].push([v,w]);graph[v].push([u,2*w]);}
 const dist=Array(n).fill(Infinity),heap=new MinHeap();dist[0]=0;heap.push([0,0]);
 while(heap.a.length){const [cost,u]=heap.pop();if(cost!==dist[u])continue;if(u===n-1)return cost;for(const [v,w] of graph[u])if(cost+w<dist[v]){dist[v]=cost+w;heap.push([dist[v],v]);}}
 return -1;
}

var minCost = solve;
module.exports = solve;
