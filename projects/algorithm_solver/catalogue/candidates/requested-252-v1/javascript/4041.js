/**
 * 4041. Minimum Operations to Form Subset Sum II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-form-subset-sum-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4041.Minimum%20Operations%20to%20Form%20Subset%20Sum%20II/README_EN.md
 * Complexity: O(n S log(M) log(S)) time and O(S + U log(M) log(S)) space with per-value option caching.
 * Multiplication/division order: unrestricted; cancelling adjacent multiply/divide pairs leaves divisions followed by multiplications. The unused-element option costs zero. Inputs preserved.
 */

function solve(nums,sum) {
  const infinity=1e9,best=new Float64Array(sum+1);best.fill(infinity);best[0]=0;
  const cache=new Map();
  for(const original of nums) {
    if(!cache.has(original)) {
      const options=new Map();let value=original,divisions=0;
      while(value>0) {
        let candidate=value,multiplications=0;
        while(candidate<=sum) {
          const cost=divisions+multiplications;
          options.set(candidate,Math.min(options.get(candidate)??infinity,cost));
          if(false && divisions>0)break;
          candidate*=2;multiplications++;
        }
        value=Math.floor(value/2);divisions++;
      }
      cache.set(original,Array.from(options).sort((a,b)=>a[0]-b[0]));
    }
    const options=cache.get(original);
    for(let total=sum;total>0;total--) {
      let value=best[total];
      for(const [amount,cost] of options) { if(amount>total)break;value=Math.min(value,best[total-amount]+cost); }
      best[total]=value;
    }
  }
  return best[sum]===infinity?-1:best[sum];
}

function minOperations(nums, sum) {
  return solve(nums, sum);
}

class Solution {
  minOperations(nums, sum) {
    return solve(nums, sum);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minOperations, Solution };
}
