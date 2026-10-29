"use strict";
class FindSumPairs{constructor(nums1,nums2){this.first=nums1.slice();this.second=nums2.slice();this.counts=new Map();for(const v of nums2)this.counts.set(v,(this.counts.get(v)||0)+1);}add(index,val){const old=this.second[index];this.counts.set(old,this.counts.get(old)-1);this.second[index]+=val;const v=this.second[index];this.counts.set(v,(this.counts.get(v)||0)+1);}count(tot){let result=0;for(const v of this.first)result+=this.counts.get(tot-v)||0;return result;}}

function solve(operations,args){const x=new FindSumPairs(...args[0]),out=[null];for(let i=1;i<operations.length;i++){const v=x[operations[i]](...args[i]);out.push(v===undefined?null:v);}return out;}
module.exports=solve;
module.exports.FindSumPairs=FindSumPairs;
