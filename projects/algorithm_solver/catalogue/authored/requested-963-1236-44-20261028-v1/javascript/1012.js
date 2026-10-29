"use strict";
function solve(n){const ds=String(n).split('').map(Number);function perm(a,b){let r=1;for(let i=0;i<b;i++)r*=a-i;return r;}let unique=0;for(let len=1;len<ds.length;len++)unique+=9*perm(9,len-1);const used=new Set();let all=true;for(let i=0;i<ds.length;i++){for(let d=i===0?1:0;d<ds[i];d++)if(!used.has(d))unique+=perm(9-i,ds.length-i-1);if(used.has(ds[i])){all=false;break;}used.add(ds[i]);}if(all)unique++;return n-unique;}

function numDupDigitsAtMostN(n){return solve(n);}
module.exports=solve;
module.exports.numDupDigitsAtMostN=numDupDigitsAtMostN;
