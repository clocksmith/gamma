// Original candidate implementation. Contract: https://leetcode.com/problems/shortest-string-that-contains-three-strings/
"use strict";
function solve(a,b,c){function merge(x,y){if(x.includes(y))return x;for(let k=Math.min(x.length,y.length);k>0;k--)if(x.slice(-k)===y.slice(0,k))return x+y.slice(k);return x+y;}const arr=[a,b,c],out=[];for(let i=0;i<3;i++)for(let j=0;j<3;j++)if(j!==i){let k=3-i-j;out.push(merge(merge(arr[i],arr[j]),arr[k]));}out.sort((x,y)=>x.length-y.length||(x<y?-1:x>y?1:0));return out[0];}
module.exports = solve;
