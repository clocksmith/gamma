/**
 * 4060. Count Evenly Good Integers
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-evenly-good-integers/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4060.Count%20Evenly%20Good%20Integers/README_EN.md
 * Complexity: O(10 log r) time, O(log r) states.
 * Leading padding zeros are not digits of a positive integer. Internal zero digits count as even; integers with zero even digits qualify. All counts fit exact JS Number range.
 */

function solve(l,r) {
  function count(bound) {
    if(bound<1)return 0;
    const digits=String(bound).split('').map(Number),memo=new Map();
    function visit(position,parity,started,tight) {
      if(position===digits.length)return started && parity===0?1:0;
      const key=position*8+parity*4+Number(started)*2+Number(tight);
      if(memo.has(key))return memo.get(key);
      const limit=tight?digits[position]:9;let answer=0;
      for(let digit=0;digit<=limit;digit++) {
        const next=started || digit!==0,nextParity=parity ^ Number(next && digit%2===0);
        answer+=visit(position+1,nextParity,next,tight && digit===limit);
      }
      memo.set(key,answer);return answer;
    }
    return visit(0,0,false,true);
  }
  return count(r)-count(l-1);
}

function countEvenlyGoodIntegers(l, r) {
  return solve(l, r);
}

class Solution {
  countEvenlyGoodIntegers(l, r) {
    return solve(l, r);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countEvenlyGoodIntegers, Solution };
}
