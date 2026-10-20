function countUnivalSubtrees(root) {
  let count = 0;
  function visit(node) {
    if (!node) return true;
    const left = visit(node.left), right = visit(node.right);
    if (!left || !right || (node.left && node.left.val !== node.val) || (node.right && node.right.val !== node.val)) return false;
    count++;
    return true;
  }
  visit(root);
  return count;
}
