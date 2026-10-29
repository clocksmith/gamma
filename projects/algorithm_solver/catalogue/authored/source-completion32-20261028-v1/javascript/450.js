// 450 — Delete Node in a BST. Original implementation; authored candidate, not independently qualified.
function solve(root, key) {
  let parent=null,current=root;
  while(current&&current.val!==key){parent=current;current=key<current.val?current.left:current.right;}
  if(!current)return root;
  if(current.left&&current.right){parent=current;let successor=current.right;while(successor.left){parent=successor;successor=successor.left;}current.val=successor.val;current=successor;}
  const child=current.left||current.right;
  if(!parent)return child;
  if(parent.left===current)parent.left=child;else parent.right=child;
  return root;
}

module.exports = { solve, deleteNode: solve };
