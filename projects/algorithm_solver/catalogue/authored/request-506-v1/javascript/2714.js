// Original candidate implementation. Contract: https://leetcode.com/problems/find-shortest-path-with-k-hops/
"use strict";
class MinHeap {
  constructor(){this.a=[];}
  push(v){const a=this.a;let i=a.length;a.push(v);while(i){const p=(i-1)>>1;if(a[p][0]<=v[0])break;a[i]=a[p];i=p;}a[i]=v;}
  pop(){const a=this.a,result=a[0],v=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let j=2*i+1;if(j+1<a.length&&a[j+1][0]<a[j][0])j++;if(a[j][0]>=v[0])break;a[i]=a[j];i=j;}a[i]=v;}return result;}
}

function solve(n,edges,s,d,k){const adj=Array.from({length:n},()=>[]);for(const [u,v,w] of edges){adj[u].push([v,w]);adj[v].push([u,w]);}const dist=Array.from({length:n},()=>Array(k+1).fill(Infinity)),heap=new MinHeap();dist[s][0]=0;heap.push([0,s,0]);while(heap.a.length){const [cost,u,used]=heap.pop();if(cost!==dist[u][used])continue;if(u===d)return cost;for(const [v,w] of adj[u]){if(cost+w<dist[v][used]){dist[v][used]=cost+w;heap.push([cost+w,v,used]);}if(used<k&&cost<dist[v][used+1]){dist[v][used+1]=cost;heap.push([cost,v,used+1]);}}}return -1;}
module.exports = solve;
