function solve(nums){const n=nums.length,left=Array(n).fill(1),right=Array(n).fill(1);left[1]=right[n-2]=2;for(let i=2;i<n;i++)left[i]=nums[i]-nums[i-1]===nums[i-1]-nums[i-2]?left[i-1]+1:2;for(let i=n-3;i>=0;i--)right[i]=nums[i+1]-nums[i]===nums[i+2]-nums[i+1]?right[i+1]+1:2;let longest=0;for(const v of left)longest=Math.max(longest,v);let answer=Math.min(n,longest+1);for(let i=1;i<n-1;i++){const gap=nums[i+1]-nums[i-1];if(gap%2!==0)continue;const d=gap/2,l=i>=2&&nums[i-1]-nums[i-2]===d?left[i-1]:1,r=i+2<n&&nums[i+2]-nums[i+1]===d?right[i+1]:1;answer=Math.max(answer,l+1+r);}return answer;}

var longestArithmetic = solve;
module.exports = solve;

