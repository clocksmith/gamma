// 404 — Sum of Left Leaves. Original implementation; authored candidate, not independently qualified.
function solve(root) {
  let total=0;const stack=[[root,false]];
  while(stack.length){const [node,left]=stack.pop();if(!node)continue;if(!node.left&&!node.right&&left)total+=node.val;stack.push([node.right,false],[node.left,true]);}
  return total;
}

module.exports = { solve, sumOfLeftLeaves: solve };
