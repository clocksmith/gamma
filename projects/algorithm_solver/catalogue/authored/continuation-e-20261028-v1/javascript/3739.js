function solve(nums,target){const n=nums.length,tree=Array(2*n+3).fill(0);function add(i){while(i<tree.length){tree[i]++;i+=i&-i;}}function query(i){let total=0;while(i){total+=tree[i];i-=i&-i;}return total;}let prefix=0,answer=0;add(n+1);for(const x of nums){prefix+=x===target?1:-1;const index=prefix+n+1;answer+=query(index-1);add(index);}return answer;}

var countMajoritySubarrays = solve;
module.exports = solve;
