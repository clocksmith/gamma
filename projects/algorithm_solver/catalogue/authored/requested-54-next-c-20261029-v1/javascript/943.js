"use strict";
function solve(words){const n=words.length,overlap=Array.from({length:n},()=>Array(n).fill(0));for(let i=0;i<n;i++)for(let j=0;j<n;j++)if(i!==j)for(let k=0;k<=Math.min(words[i].length,words[j].length);k++)if(words[i].endsWith(words[j].slice(0,k)))overlap[i][j]=k;
 const dp=Array.from({length:1<<n},()=>Array(n).fill(null));for(let i=0;i<n;i++)dp[1<<i][i]=words[i];for(let mask=0;mask<1<<n;mask++)for(let last=0;last<n;last++){const current=dp[mask][last];if(current===null)continue;for(let next=0;next<n;next++)if(!(mask&(1<<next))){const candidate=current+words[next].slice(overlap[last][next]),row=dp[mask|(1<<next)];if(row[next]===null||candidate.length<row[next].length)row[next]=candidate;}}
 let answer=null;for(const s of dp[(1<<n)-1])if(s!==null&&(answer===null||s.length<answer.length))answer=s;return answer;
}

function shortestSuperstring(words) { return solve(words); }
module.exports=solve;module.exports.shortestSuperstring=shortestSuperstring;
