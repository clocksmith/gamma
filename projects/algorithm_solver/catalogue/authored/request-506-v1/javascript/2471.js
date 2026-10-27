// Original implementation. Contract: https://leetcode.com/problems/minimum-number-of-operations-to-sort-a-binary-tree-by-level/
"use strict";
function solve(a){if(!a.length)return 0;const levels=[],q=[[a[0],0]];let pos=1;for(let h=0;h<q.length;h++){const [v,d]=q[h];if(levels.length===d)levels.push([]);levels[d].push(v);for(let k=0;k<2;k++)if(pos<a.length){const x=a[pos++];if(x!==null)q.push([x,d+1]);}}let answer=0;for(const row of levels){const ranks=new Map([...row].sort((a,b)=>a-b).map((v,i)=>[v,i])),p=row.map(v=>ranks.get(v)),seen=Array(p.length).fill(false);for(let i=0;i<p.length;i++)if(!seen[i]){let j=i,size=0;while(!seen[j]){seen[j]=true;size++;j=p[j];}answer+=size-1;}}return answer;}
module.exports = solve;
