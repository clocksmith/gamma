// Original candidate implementation. Contract: https://leetcode.com/problems/match-substring-after-replacement/
"use strict";
function solve(s,sub,mappings){const allowed=new Set(mappings.map(([a,b])=>a+b));for(let i=0;i+sub.length<=s.length;i++){let ok=true;for(let j=0;j<sub.length;j++)if(sub[j]!==s[i+j]&&!allowed.has(sub[j]+s[i+j])){ok=false;break;}if(ok)return true;}return false;}
module.exports = solve;
