"use strict";
function solve(n){const out=new Array(2*n-1).fill(0);function place(i,used){while(i<out.length&&out[i])i++;if(i===out.length)return true;for(let v=n;v>=1;v--){if(used&(1<<v))continue;const j=v===1?i:i+v;if(j>=out.length||out[j])continue;out[i]=out[j]=v;if(place(i+1,used|(1<<v)))return true;out[i]=out[j]=0;}return false;}place(0,0);return out;}

function constructDistancedSequence(n){return solve(n);}
module.exports=solve;
module.exports.constructDistancedSequence=constructDistancedSequence;
