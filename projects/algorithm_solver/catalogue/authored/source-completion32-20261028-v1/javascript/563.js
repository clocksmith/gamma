// 563 — Binary Tree Tilt. Original implementation; authored candidate, not independently qualified.
function solve(root) {
  const sums=new Map(),stack=[[root,false]];let answer=0;
  while(stack.length){const [node,visited]=stack.pop();if(!node)continue;if(!visited)stack.push([node,true],[node.right,false],[node.left,false]);else{const left=sums.get(node.left)||0,right=sums.get(node.right)||0;answer+=Math.abs(left-right);sums.set(node,node.val+left+right);}}return answer;
}

module.exports = { solve, findTilt: solve };
