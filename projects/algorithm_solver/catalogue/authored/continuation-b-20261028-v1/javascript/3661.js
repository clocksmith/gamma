function solve(robots,distance,walls){
 const rows=robots.map((p,i)=>[p,distance[i]]).sort((a,b)=>a[0]-b[0]),positions=walls.slice().sort((a,b)=>a-b);
 function lower(x){let lo=0,hi=positions.length;while(lo<hi){const mid=Math.floor((lo+hi)/2);if(positions[mid]<x)lo=mid+1;else hi=mid;}return lo;}
 function upper(x){let lo=0,hi=positions.length;while(lo<hi){const mid=Math.floor((lo+hi)/2);if(positions[mid]<=x)lo=mid+1;else hi=mid;}return lo;}
 const count=(a,b)=>a<=b?upper(b)-lower(a):0;let fixed=0;for(const [p] of rows)fixed+=count(p,p);
 let [first,reach]=rows[0],dp=[count(first-reach,first-1),0];
 for(let i=1;i<rows.length;i++){const [a,da]=rows[i-1],[b,db]=rows[i],rightEnd=Math.min(b-1,a+da),leftStart=Math.max(a+1,b-db),r=count(a+1,rightEnd),l=count(leftStart,b-1),overlap=count(leftStart,rightEnd);dp=[Math.max(dp[0]+l,dp[1]+r+l-overlap),Math.max(dp[0],dp[1]+r)];}
 const [last,lastReach]=rows[rows.length-1];return fixed+Math.max(dp[0],dp[1]+count(last+1,last+lastReach));
}

var maxWalls = solve;
module.exports = solve;
