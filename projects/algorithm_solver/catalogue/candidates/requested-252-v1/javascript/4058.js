/**
 * 4058. Maximum Pulse Value After One Subarray Rotation
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-pulse-value-after-one-subarray-rotation/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4058.Maximum%20Pulse%20Value%20After%20One%20Subarray%20Rotation/README_EN.md
 * Complexity: O(n) time, O(1) space.
 * For [l,r], gain = -2*P[r+1]+2*P[l]+(sign(l)+sign(r))*nums[l]. Two parity-specific maxima cover all earlier l. Evaluate before inserting l=r, enforcing l<r. No-operation gain zero is retained. Inputs preserved.
 */

function solve(nums) {
  let prefix=0,gain=0;const best=[-Infinity,-Infinity];
  for(let i=0;i<nums.length;i++) {
    const value=nums[i],sign=i%2===0?1:-1,before=prefix;
    prefix+=sign*value;
    gain=Math.max(gain,best[i%2]-2*prefix);
    best[0]=Math.max(best[0],2*before+(sign+1)*value);
    best[1]=Math.max(best[1],2*before+(sign-1)*value);
  }
  return prefix+gain;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
