function solve(balance){let total=0,sink=-1;for(let i=0;i<balance.length;i++){total+=balance[i];if(balance[i]<0)sink=i;}if(total<0)return -1;if(sink<0)return 0;const n=balance.length,supply=Array(Math.floor(n/2)+1).fill(0);for(let i=0;i<n;i++)if(balance[i]>0){const d=Math.abs(i-sink);supply[Math.min(d,n-d)]+=balance[i];}let need=-balance[sink],answer=0;for(let d=0;d<supply.length;d++){const take=Math.min(supply[d],need);answer+=take*d;need-=take;if(need===0)return answer;}return -1;}

var minMoves = solve;
module.exports = solve;
