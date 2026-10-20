function binaryTreePaths(root) {
  const result = [];
  function visit(node, path) {
    if (!node) return;
    const next = path ? `${path}->${node.val}` : String(node.val);
    if (!node.left && !node.right) result.push(next);
    else { visit(node.left, next); visit(node.right, next); }
  }
  visit(root, '');
  return result;
}
