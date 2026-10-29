"use strict";
function solve(quality,wage,k){const workers=quality.map((q,i)=>[q,wage[i]]).sort((a,b)=>a[1]*b[0]-b[1]*a[0]),heap=[];let total=0,answer=Infinity;
 function push(x){heap.push(x);let i=heap.length-1;while(i>0){const p=(i-1)>>1;if(heap[p]>=heap[i])break;[heap[p],heap[i]]=[heap[i],heap[p]];i=p;}}
 function pop(){const x=heap[0],last=heap.pop();if(heap.length){heap[0]=last;let i=0;while(true){let j=2*i+1;if(j>=heap.length)break;if(j+1<heap.length&&heap[j+1]>heap[j])j++;if(heap[i]>=heap[j])break;[heap[i],heap[j]]=[heap[j],heap[i]];i=j;}}return x;}
 for(const [q,w] of workers){push(q);total+=q;if(heap.length>k)total-=pop();if(heap.length===k)answer=Math.min(answer,total*w/q);}return answer;
}

function mincostToHireWorkers(quality, wage, k) { return solve(quality, wage, k); }
module.exports=solve;
module.exports.mincostToHireWorkers=mincostToHireWorkers;
