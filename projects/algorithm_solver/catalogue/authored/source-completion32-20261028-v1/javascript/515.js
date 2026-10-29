// 515 — Find Largest Value in Each Tree Row. Original implementation; authored candidate, not independently qualified.
function solve(root) {
  if(!root)return [];let level=[root];const result=[];
  while(level.length){let maximum=-Infinity;const next=[];for(const node of level){maximum=Math.max(maximum,node.val);if(node.left)next.push(node.left);if(node.right)next.push(node.right);}result.push(maximum);level=next;}
  return result;
}

module.exports = { solve, largestValues: solve };
