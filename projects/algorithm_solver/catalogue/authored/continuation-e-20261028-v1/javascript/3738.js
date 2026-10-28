function solve(nums){const n=nums.length,left=Array(n).fill(1),right=Array(n).fill(1);for(let i=1;i<n;i++)if(nums[i-1]<=nums[i])left[i]=left[i-1]+1;for(let i=n-2;i>=0;i--)if(nums[i]<=nums[i+1])right[i]=right[i+1]+1;let answer=1;for(let i=0;i<n;i++){answer=Math.max(answer,left[i]);if(i)answer=Math.max(answer,left[i-1]+1);if(i+1<n)answer=Math.max(answer,right[i+1]+1);if(i>0&&i+1<n&&nums[i-1]<=nums[i+1])answer=Math.max(answer,left[i-1]+1+right[i+1]);}return Math.min(answer,n);}

var longestSubarray = solve;
module.exports = solve;
