// Original candidate implementation. Contract: https://leetcode.com/problems/minimum-cost-to-buy-apples/
"use strict";
class MinHeap {
  constructor(){this.a=[];}
  push(v){const a=this.a;let i=a.length;a.push(v);while(i){const p=(i-1)>>1;if(a[p][0]<=v[0])break;a[i]=a[p];i=p;}a[i]=v;}
  pop(){const a=this.a,result=a[0],v=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let j=2*i+1;if(j+1<a.length&&a[j+1][0]<a[j][0])j++;if(a[j][0]>=v[0])break;a[i]=a[j];i=j;}a[i]=v;}return result;}
}

function solve(n,roads,appleCost,k){const adj=Array.from({length:n},()=>[]);for(const [a,b,c] of roads){adj[a-1].push([b-1,c*(k+1)]);adj[b-1].push([a-1,c*(k+1)]);}const d=[...appleCost],heap=new MinHeap();d.forEach((v,i)=>heap.push([v,i]));while(heap.a.length){const [cost,v]=heap.pop();if(cost!==d[v])continue;for(const [w,c] of adj[v])if(cost+c<d[w]){d[w]=cost+c;heap.push([d[w],w]);}}return d;}
module.exports = solve;
