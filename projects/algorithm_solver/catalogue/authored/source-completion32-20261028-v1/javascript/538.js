// 538 — Convert BST to Greater Tree. Original implementation; authored candidate, not independently qualified.
function solve(root) {
  const stack=[];let current=root,total=0;
  while(stack.length||current){while(current){stack.push(current);current=current.right;}current=stack.pop();total+=current.val;current.val=total;current=current.left;}return root;
}

module.exports = { solve, convertBST: solve };
