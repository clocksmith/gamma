// 530 — Minimum Absolute Difference in BST. Original implementation; authored candidate, not independently qualified.
function solve(root) {
  const stack=[];let current=root,previous=null,answer=Infinity;
  while(stack.length||current){while(current){stack.push(current);current=current.left;}current=stack.pop();if(previous!==null)answer=Math.min(answer,current.val-previous);previous=current.val;current=current.right;}return answer;
}

module.exports = { solve, getMinimumDifference: solve };
