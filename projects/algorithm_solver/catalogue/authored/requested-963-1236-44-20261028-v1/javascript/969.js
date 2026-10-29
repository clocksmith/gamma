"use strict";
function solve(arr){const a=[...arr],out=[];function flip(k){for(let l=0,r=k-1;l<r;l++,r--)[a[l],a[r]]=[a[r],a[l]];out.push(k);}for(let end=a.length;end>1;end--){let at=0;for(let i=1;i<end;i++)if(a[i]>a[at])at=i;if(at===end-1)continue;if(at)flip(at+1);flip(end);}return out;}

function pancakeSort(arr){return solve(arr);}
module.exports=solve;
module.exports.pancakeSort=pancakeSort;
