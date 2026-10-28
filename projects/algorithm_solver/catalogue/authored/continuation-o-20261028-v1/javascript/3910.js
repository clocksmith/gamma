"use strict";
function solve(nums, edges) {
const n=nums.length,adjacency=new Int32Array(n),parity=new Uint8Array(1<<n);for(const [a,b] of edges){adjacency[a]|=1<<b;adjacency[b]|=1<<a;}let answer=0;for(let mask=1;mask<(1<<n);mask++){const bit=mask&-mask;parity[mask]=parity[mask^bit]^nums[31-Math.clz32(bit)];if(parity[mask])continue;let reached=bit,frontier=bit;while(frontier){let following=0;while(frontier){const current=frontier&-frontier;frontier^=current;following|=adjacency[31-Math.clz32(current)];}frontier=following&mask&~reached;reached|=frontier;}if(reached===mask)answer++;}return answer;
}
function evenSumSubgraphs(nums, edges) { return solve(nums, edges); }
module.exports=solve;
module.exports.evenSumSubgraphs=evenSumSubgraphs;
