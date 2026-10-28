"use strict";
function solve(nums, k, m) {
const values=new Map();for(const value of nums)if(!values.has(value))values.set(value,values.size);let size=1;while(size<values.size)size*=2;const infinity=nums.length+1,tree=new Int32Array(size*2).fill(infinity),positions=Array.from({length:values.size},()=>[]),counts=new Int32Array(values.size);function update(index,value){let node=size+index;tree[node]=value;for(node=Math.floor(node/2);node;node=Math.floor(node/2))tree[node]=Math.min(tree[node*2],tree[node*2+1]);}let left=0,distinct=0,answer=0;for(let right=0;right<nums.length;right++){const index=values.get(nums[right]);positions[index].push(right);if(counts[index]===0)distinct++;counts[index]++;update(index,positions[index].length>=m?positions[index][positions[index].length-m]:-1);while(distinct>k){const outgoing=values.get(nums[left++]);counts[outgoing]--;if(counts[outgoing]===0){distinct--;update(outgoing,infinity);}}if(distinct===k)answer+=Math.max(0,tree[1]-left+1);}return answer;
}
function countSubarrays(nums, k, m) { return solve(nums, k, m); }
module.exports=solve;
module.exports.countSubarrays=countSubarrays;
