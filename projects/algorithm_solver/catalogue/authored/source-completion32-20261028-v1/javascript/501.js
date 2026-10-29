// 501 — Find Mode in Binary Search Tree. Original implementation; authored candidate, not independently qualified.
function solve(root) {
  const stack=[];let current=root,previous=null,run=0,maximum=0,result=[];
  while(stack.length||current){while(current){stack.push(current);current=current.left;}current=stack.pop();run=current.val===previous?run+1:1;previous=current.val;if(run>maximum){maximum=run;result=[current.val];}else if(run===maximum)result.push(current.val);current=current.right;}
  return result;
}

module.exports = { solve, findMode: solve };
