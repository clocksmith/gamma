function solve(s,k){const n=s.length,zeros=[...s].filter(c=>c==='0').length;if(!zeros)return 0;const parent=Array.from({length:n+3},(_,i)=>i);function find(x){while(parent[x]!==x){parent[x]=parent[parent[x]];x=parent[x];}return x;}parent[zeros]=find(zeros+2);const queue=[[zeros,0]];let head=0;while(head<queue.length){const [z,d]=queue[head++],lo=z+k-2*Math.min(z,k),hi=z+k-2*Math.max(0,k-(n-z));let next=find(lo);while(next<=hi){if(next===0)return d+1;queue.push([next,d+1]);parent[next]=find(next+2);next=find(next);}}return -1;}

var minOperations = solve;
module.exports = solve;
