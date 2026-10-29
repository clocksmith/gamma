"use strict";
function solve(s1,s2){const q=[[s1,0]],seen=new Set([s1]);
 for(let h=0;h<q.length;h++){const [s,d]=q[h];if(s===s2)return d;let i=0;while(s[i]===s2[i])i++;
  for(let j=i+1;j<s.length;j++)if(s[j]===s2[i]&&s[j]!==s2[j]){const a=s.split('');[a[i],a[j]]=[a[j],a[i]];const t=a.join('');if(!seen.has(t)){seen.add(t);q.push([t,d+1]);}}
 }
}

function kSimilarity(s1, s2) { return solve(s1, s2); }
module.exports=solve;
module.exports.kSimilarity=kSimilarity;
