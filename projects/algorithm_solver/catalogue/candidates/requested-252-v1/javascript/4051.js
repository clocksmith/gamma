/**
 * 4051. Count Subarrays with Distant Sums
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-subarrays-with-distant-sums/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4051.Count%20Subarrays%20with%20Distant%20Sums/README_EN.md
 * Complexity: O(n log n) time, O(n) space.
 * Subtract strictly-near sums from all nonempty subarrays. k=0 returns all subarrays without overlapping-boundary counting. Signed prefix sums remain exact within stated JS Number range. Inputs preserved.
 */

function solve(nums,goal,k) {
  const n=nums.length;let answer=n*(n+1)/2;
  if(k===0)return answer;
  const prefixes=[0];for(const x of nums)prefixes.push(prefixes[prefixes.length-1]+x);
  const a=Array.from(new Set(prefixes)).sort((x,y)=>x-y),tree=new Int32Array(a.length+1);
  function bound(x,upper) {let l=0,r=a.length;while(l<r){const m=Math.floor((l+r)/2);if(a[m]<x || (upper && a[m]===x))l=m+1;else r=m;}return l;}
  function count(p){let total=0;while(p){total+=tree[p];p-=p&-p;}return total;}
  for(const value of prefixes){
    answer-=count(bound(value-goal+k,false))-count(bound(value-goal-k,true));
    for(let p=bound(value,false)+1;p<tree.length;p+=p&-p)tree[p]++;
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
