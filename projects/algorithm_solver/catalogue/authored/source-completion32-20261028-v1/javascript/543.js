// 543 — Diameter of Binary Tree. Original implementation; authored candidate, not independently qualified.
function solve(root) {
  const heights=new Map(),stack=[[root,false]];let answer=0;
  while(stack.length){const [node,visited]=stack.pop();if(!node)continue;if(!visited)stack.push([node,true],[node.right,false],[node.left,false]);else{const left=heights.get(node.left)||0,right=heights.get(node.right)||0;answer=Math.max(answer,left+right);heights.set(node,1+Math.max(left,right));}}return answer;
}

module.exports = { solve, diameterOfBinaryTree: solve };
