"use strict";
function solve(s1,s2){const memo=new Map(),digit=c=>c!==undefined&&c>='1'&&c<='9';function visit(i,j,d){if(i===s1.length&&j===s2.length)return d===0;const key=i+','+j+','+d;if(memo.has(key))return memo.get(key);let result=false;if(digit(s1[i])){let v=0;for(let e=i;e<Math.min(i+3,s1.length)&&digit(s1[e]);e++){v=v*10+Number(s1[e]);if(visit(e+1,j,d+v)){result=true;break;}}}if(!result&&digit(s2[j])){let v=0;for(let e=j;e<Math.min(j+3,s2.length)&&digit(s2[e]);e++){v=v*10+Number(s2[e]);if(visit(i,e+1,d-v)){result=true;break;}}}if(!result&&d>0&&j<s2.length&&!digit(s2[j]))result=visit(i,j+1,d-1);if(!result&&d<0&&i<s1.length&&!digit(s1[i]))result=visit(i+1,j,d+1);if(!result&&d===0&&i<s1.length&&j<s2.length&&!digit(s1[i])&&s1[i]===s2[j])result=visit(i+1,j+1,0);memo.set(key,result);return result;}return visit(0,0,0);}

function possiblyEquals(s1, s2){return solve(s1, s2);}
module.exports=solve;
module.exports.possiblyEquals=possiblyEquals;
