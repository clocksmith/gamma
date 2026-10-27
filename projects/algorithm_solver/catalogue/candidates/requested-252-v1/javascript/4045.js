/**
 * 4045. Count Robot Groups
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-robot-groups/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4045.Count%20Robot%20Groups/README_EN.md
 * Complexity: O(n) time, O(n) space.
 * Collapse entire connected runs at time zero to their rightmost representative. Thereafter speeds can only decrease through catch-up merges. A representative faster than a suffix minimum eventually joins; equal speeds with a positive initial gap remain separate. Inputs preserved.
 */

function solve(position,speed,distance) {
  const representatives=[];
  for(let i=0;i<position.length;i++) if(i+1===position.length || position[i+1]-position[i]>distance)representatives.push(speed[i]);
  let groups=0,minimum=Infinity;
  for(let i=representatives.length-1;i>=0;i--) if(representatives[i]<=minimum) {groups++;minimum=representatives[i];}
  return groups;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
