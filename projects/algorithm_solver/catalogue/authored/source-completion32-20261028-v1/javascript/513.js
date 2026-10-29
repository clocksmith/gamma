// 513 — Find Bottom Left Tree Value. Original implementation; authored candidate, not independently qualified.
function solve(root) {
  const queue=[root];let head=0,answer=root.val;
  while(head<queue.length){answer=queue[head].val;const end=queue.length;while(head<end){const node=queue[head++];if(node.left)queue.push(node.left);if(node.right)queue.push(node.right);}}
  return answer;
}

module.exports = { solve, findBottomLeftValue: solve };
