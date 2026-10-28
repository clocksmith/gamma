'use strict';
// Separate binary-search/successor-DSU drying assignment; caller is read-only.
function solve(rains){
 const dry=[];for(let i=0;i<rains.length;i++)if(rains[i]===0)dry.push(i);
 const parent=new Int32Array(dry.length+1);for(let i=0;i<parent.length;i++)parent[i]=i;
 function find(i){let root=i;while(parent[root]!==root)root=parent[root];while(parent[i]!==i){const next=parent[i];parent[i]=root;i=next;}return root;}
 const answer=rains.map(v=>v===0?1:-1),last=new Map();
 for(let day=0;day<rains.length;day++){
  const lake=rains[day];if(lake===0)continue;
  if(last.has(lake)){
   let lo=0,hi=dry.length;const previous=last.get(lake);
   while(lo<hi){const mid=Math.floor((lo+hi)/2);if(dry[mid]<=previous)lo=mid+1;else hi=mid;}
   const slot=find(lo);if(slot===dry.length||dry[slot]>=day)return[];
   answer[dry[slot]]=lake;parent[slot]=find(slot+1);
  }
  last.set(lake,day);
 }
 return answer;
}
const avoidFlood=solve;
class Solution{avoidFlood(rains){return solve(rains);}}
if(typeof module!=='undefined')module.exports={solve,Solution,avoidFlood};
