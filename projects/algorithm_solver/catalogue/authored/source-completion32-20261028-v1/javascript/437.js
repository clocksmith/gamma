// 437 — Path Sum III. Original implementation; authored candidate, not independently qualified.
function solve(root, targetSum) {
  const counts=new Map([[0,1]]),stack=[[root,0,false]];let answer=0;
  while(stack.length){let [node,sum,leaving]=stack.pop();if(!node)continue;if(leaving){counts.set(sum,counts.get(sum)-1);continue;}sum+=node.val;answer+=counts.get(sum-targetSum)||0;counts.set(sum,(counts.get(sum)||0)+1);stack.push([node,sum,true],[node.right,sum,false],[node.left,sum,false]);}
  return answer;
}

module.exports = { solve, pathSum: solve };
