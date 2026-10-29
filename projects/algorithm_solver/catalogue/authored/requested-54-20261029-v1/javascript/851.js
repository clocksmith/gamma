"use strict";
function solve(richer,quiet){const n=quiet.length,edges=Array.from({length:n},()=>[]),degree=Array(n).fill(0),ans=Array.from({length:n},(_,i)=>i),q=[];
 for(const [a,b] of richer){edges[a].push(b);degree[b]++;}
 for(let i=0;i<n;i++)if(!degree[i])q.push(i);
 for(let h=0;h<q.length;h++){const a=q[h];for(const b of edges[a]){if(quiet[ans[a]]<quiet[ans[b]])ans[b]=ans[a];if(--degree[b]===0)q.push(b);}}
 return ans;
}

function loudAndRich(richer, quiet) { return solve(richer, quiet); }
module.exports=solve;
module.exports.loudAndRich=loudAndRich;
