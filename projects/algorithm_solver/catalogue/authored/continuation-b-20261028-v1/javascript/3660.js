function solve(nums){const n=nums.length,suffix=Array(n+1).fill(Infinity),answer=Array(n);for(let i=n-1;i>=0;i--)suffix[i]=Math.min(nums[i],suffix[i+1]);let start=0,maximum=0;for(let i=0;i<n;i++){maximum=Math.max(maximum,nums[i]);if(maximum<=suffix[i+1]){for(let j=start;j<=i;j++)answer[j]=maximum;start=i+1;maximum=0;}}return answer;}

var maxValue = solve;
module.exports = solve;
