/**
 * 4059. Lexicographically Largest Power Array
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/lexicographically-largest-power-array/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4059.Lexicographically%20Largest%20Power%20Array/README_EN.md
 * Complexity: O(15n) time, O(n) space.
 * Ordered blocks encode exactly the higher-bit optimal-prefix restrictions. Split only the first block containing a zero for the current bit; sorting later blocks by that bit would impose an unjustified restriction. Inputs preserved.
 */

function solve(nums) {
  const blocks=[nums.slice()],answer=[];
  for(let bit=14;bit>=0;bit--) {
    let prefix=0;
    for(let index=0;index<blocks.length;index++) {
      const ones=[],zeros=[];
      for(const value of blocks[index])((value&(1<<bit))!==0?ones:zeros).push(value);
      prefix+=ones.length;
      if(zeros.length) {blocks.splice(index,1,...(ones.length?[ones,zeros]:[zeros]));break;}
    }
    answer.push(prefix);
  }
  return answer;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
