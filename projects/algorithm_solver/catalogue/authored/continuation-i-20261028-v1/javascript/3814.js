function solve(costs,capacity,budget){const machines=costs.map((cost,i)=>[cost,capacity[i]]).sort((a,b)=>a[0]-b[0]),prefix=[];let best=0,answer=0;for(const [,cap] of machines){best=Math.max(best,cap);prefix.push(best);}for(let i=0;i<machines.length;i++){const [cost,cap]=machines[i];if(cost<budget)answer=Math.max(answer,cap);let lo=0,hi=machines.length;while(lo<hi){const mid=Math.floor((lo+hi)/2);if(machines[mid][0]<budget-cost)lo=mid+1;else hi=mid;}const j=Math.min(i-1,lo-1);if(j>=0)answer=Math.max(answer,cap+prefix[j]);}return answer;}

var maxCapacity = solve;
module.exports = solve;
