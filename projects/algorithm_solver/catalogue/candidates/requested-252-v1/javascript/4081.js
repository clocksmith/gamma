/**
 * 4081. Prime Subset Selection II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/prime-subset-selection-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4081.Prime%20Subset%20Selection%20II/README_EN.md
 * Complexity: O(n log log n + pi(n)*s) time, O(pi(n)*s+n) space.
 * Suffix 0/1 knapsack stores minimum cardinality at each exact sum. First choose the largest reachable sum, then greedily take the smallest prime whenever the optimal remaining cardinality is achievable using larger primes. This enforces all three priorities without reusing a prime. n,s<=1000.
 */

function solve(n,s) {
  const limit=Math.min(n,s);if(limit<2)return [];
  const prime=new Uint8Array(limit+1);prime.fill(1);prime[0]=prime[1]=0;
  for(let d=2;d*d<=limit;d++)if(prime[d])for(let x=d*d;x<=limit;x+=d)prime[x]=0;
  const values=[];for(let x=2;x<=limit;x++)if(prime[x])values.push(x);
  const count=values.length,infinity=count+1,suffix=Array(count+1);
  suffix[count]=new Uint16Array(s+1);suffix[count].fill(infinity);suffix[count][0]=0;
  for(let index=count-1;index>=0;index--) {
    const following=suffix[index+1],current=following.slice(),value=values[index];
    for(let total=value;total<=s;total++)current[total]=Math.min(current[total],following[total-value]+1);
    suffix[index]=current;
  }
  let total=s;while(total>0 && suffix[0][total]===infinity)total--;
  if(total===0)return [];
  let remaining=suffix[0][total];const answer=[];
  for(let index=0;index<count && total>0;index++) {
    const value=values[index];
    if(total>=value && suffix[index+1][total-value]+1===remaining){answer.push(value);total-=value;remaining--;}
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
