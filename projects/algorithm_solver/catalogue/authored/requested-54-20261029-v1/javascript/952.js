"use strict";
function solve(nums){const n=nums.length,parent=Array.from({length:n},(_,i)=>i),size=Array(n).fill(1),owners=new Map();
 function find(x){while(parent[x]!==x){parent[x]=parent[parent[x]];x=parent[x];}return x;}
 for(let i=0;i<n;i++){let v=nums[i];const factors=[];for(let p=2;p*p<=v;p++)if(v%p===0){factors.push(p);while(v%p===0)v/=p;}if(v>1)factors.push(v);
  for(const f of factors)if(!owners.has(f))owners.set(f,i);else{let a=find(i),b=find(owners.get(f));if(a!==b){if(size[a]<size[b])[a,b]=[b,a];parent[b]=a;size[a]+=size[b];}}
 }let best=1;for(let i=0;i<n;i++)best=Math.max(best,size[find(i)]);return best;
}

function largestComponentSize(nums) { return solve(nums); }
module.exports=solve;
module.exports.largestComponentSize=largestComponentSize;
