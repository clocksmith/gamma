"use strict";
function solve(nums, p, queries) {
function gcd(a,b){while(b){const next=a%b;a=b;b=next;}return a;}const values=nums.slice(),n=values.length;let size=1;while(size<n)size*=2;const tree=new Int32Array(size*2);let eligible=0;for(let i=0;i<n;i++)if(values[i]%p===0){tree[size+i]=values[i];eligible++;}for(let node=size-1;node;node--)tree[node]=gcd(tree[node*2],tree[node*2+1]);let answer=0;for(const [index,value] of queries){eligible+=(value%p===0?1:0)-(values[index]%p===0?1:0);values[index]=value;let node=size+index;tree[node]=value%p===0?value:0;for(node=Math.floor(node/2);node;node=Math.floor(node/2))tree[node]=gcd(tree[node*2],tree[node*2+1]);let good=tree[1]===p;if(good&&eligible===n&&n<=16){const prefix=[0];for(const current of values)prefix.push(gcd(prefix[prefix.length-1],current));let suffix=0;good=false;for(let i=n-1;i>=0;i--){if(gcd(prefix[i],suffix)===p){good=true;break;}suffix=gcd(suffix,values[i]);}}if(good)answer++;}return answer;
}
function countGoodSubseq(nums, p, queries) { return solve(nums, p, queries); }
module.exports=solve;
module.exports.countGoodSubseq=countGoodSubseq;
