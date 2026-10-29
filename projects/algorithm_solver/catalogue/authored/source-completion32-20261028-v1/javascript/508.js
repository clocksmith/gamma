// 508 — Most Frequent Subtree Sum. Original implementation; authored candidate, not independently qualified.
function solve(root) {
  const sums=new Map(),counts=new Map(),stack=[[root,false]];
  while(stack.length){const [node,visited]=stack.pop();if(!node)continue;if(!visited)stack.push([node,true],[node.right,false],[node.left,false]);else{const value=node.val+(sums.get(node.left)||0)+(sums.get(node.right)||0);sums.set(node,value);counts.set(value,(counts.get(value)||0)+1);}}
  let maximum=0;for(const count of counts.values())maximum=Math.max(maximum,count);
  return [...counts].filter(([,count])=>count===maximum).map(([value])=>value);
}

module.exports = { solve, findFrequentTreeSum: solve };
