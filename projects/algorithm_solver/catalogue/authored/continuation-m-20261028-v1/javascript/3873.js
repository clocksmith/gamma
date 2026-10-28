function solve(points){const parent=points.map((_,i)=>i),size=Array(points.length).fill(1),xs=new Map(),ys=new Map();function root(x){while(parent[x]!==x){parent[x]=parent[parent[x]];x=parent[x];}return x;}function merge(a,b){a=root(a);b=root(b);if(a===b)return;if(size[a]<size[b])[a,b]=[b,a];parent[b]=a;size[a]+=size[b];}for(let i=0;i<points.length;i++){const [x,y]=points[i];if(xs.has(x))merge(i,xs.get(x));if(ys.has(y))merge(i,ys.get(y));xs.set(x,i);ys.set(y,i);}let first=0,second=0;for(let i=0;i<points.length;i++)if(root(i)===i){const v=size[i];if(v>=first){second=first;first=v;}else if(v>second)second=v;}return first+second+1;}

var maxActivated = solve;
module.exports = solve;

