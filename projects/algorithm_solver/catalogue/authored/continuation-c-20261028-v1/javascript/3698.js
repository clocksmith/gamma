function solve(nums){const n=nums.length,decreasing=Array(n).fill(true);let total=0;for(const v of nums)total+=v;for(let i=n-2;i>=0;i--)decreasing[i]=decreasing[i+1]&&nums[i]>nums[i+1];let prefix=0,increasing=true,best=Infinity;for(let i=0;i<n-1;i++){prefix+=nums[i];if(i)increasing=increasing&&nums[i-1]<nums[i];if(increasing&&decreasing[i+1])best=Math.min(best,Math.abs(2*prefix-total));}return best===Infinity?-1:best;}

var splitArray = solve;
module.exports = solve;
