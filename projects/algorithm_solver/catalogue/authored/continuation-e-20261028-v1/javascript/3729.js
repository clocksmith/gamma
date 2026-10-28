function solve(nums,k){const counts=new Map([[0,1]]);let rem=0,answer=0;for(const x of nums){rem=(rem+x)%k;answer+=counts.get(rem)||0;counts.set(rem,(counts.get(rem)||0)+1);}function gcd(a,b){while(b){const t=a%b;a=b;b=t;}return a;}let i=0;while(i<nums.length){let j=i+1;while(j<nums.length&&nums[j]===nums[i])j++;const length=j-i,period=k/gcd(nums[i],k),q=Math.floor(length/period);answer-=q*length-period*q*(q+1)/2;i=j;}return answer;}

var numGoodSubarrays = solve;
module.exports = solve;
