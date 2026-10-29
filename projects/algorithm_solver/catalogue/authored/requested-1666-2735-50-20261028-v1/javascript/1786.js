"use strict";
class MinHeap {
 constructor(compare=(a,b)=>a-b){this.data=[];this.compare=compare;}
 get size(){return this.data.length;}
 peek(){return this.data[0];}
 push(value){const a=this.data;let i=a.length;a.push(value);while(i){const p=(i-1)>>1;if(this.compare(a[p],value)<=0)break;a[i]=a[p];i=p;}a[i]=value;}
 pop(){const a=this.data,result=a[0],last=a.pop();if(a.length){let i=0;while(2*i+1<a.length){let c=2*i+1;if(c+1<a.length&&this.compare(a[c+1],a[c])<0)c++;if(this.compare(last,a[c])<=0)break;a[i]=a[c];i=c;}a[i]=last;}return result;}
}
function solve(n,edges){const graph=Array.from({length:n},()=>[]);for(const [a,b,w]of edges){graph[a-1].push([b-1,w]);graph[b-1].push([a-1,w]);}const distance=new Array(n).fill(Infinity),heap=new MinHeap((a,b)=>a[0]-b[0]);distance[n-1]=0;heap.push([0,n-1]);while(heap.size){const [d,u]=heap.pop();if(d!==distance[u])continue;for(const [v,w]of graph[u])if(d+w<distance[v]){distance[v]=d+w;heap.push([d+w,v]);}}const ways=new Array(n).fill(0);ways[n-1]=1;for(const u of distance.map((_,i)=>i).sort((a,b)=>distance[a]-distance[b]))for(const [v]of graph[u])if(distance[v]>distance[u])ways[v]=(ways[v]+ways[u])%1000000007;return ways[0];}

function countRestrictedPaths(n, edges){return solve(n, edges);}
module.exports=solve;
module.exports.countRestrictedPaths=countRestrictedPaths;
