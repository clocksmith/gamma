"use strict";
function solve(nums, k) {
const ordered=[...new Set(nums)].sort((a,b)=>a-b),ranks=new Map(ordered.map((v,i)=>[v,i+1])),size=ordered.length,low=Array(size+1).fill(0),high=Array(size+1).fill(0),up=Array(nums.length),down=Array(nums.length);function update(tree,index,value){while(index<=size){tree[index]=Math.max(tree[index],value);index+=index&-index;}}function query(tree,index){let value=0;while(index){value=Math.max(value,tree[index]);index-=index&-index;}return value;}let answer=0;for(let i=0;i<nums.length;i++){if(i>=k){const j=i-k;update(low,ranks.get(nums[j]),down[j]);update(high,size+1-ranks.get(nums[j]),up[j]);}const rank=ranks.get(nums[i]);up[i]=nums[i]+query(low,rank-1);down[i]=nums[i]+query(high,size-rank);answer=Math.max(answer,up[i],down[i]);}return answer;
}
function maxAlternatingSum(nums, k) { return solve(nums, k); }
module.exports=solve;
module.exports.maxAlternatingSum=maxAlternatingSum;
