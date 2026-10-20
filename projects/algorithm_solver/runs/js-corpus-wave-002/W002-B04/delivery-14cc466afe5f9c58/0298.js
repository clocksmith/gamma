function longestConsecutive(root) {
  let best = 0;
  function visit(node, parentValue, length) {
    if (!node) return;
    const current = node.val === parentValue + 1 ? length + 1 : 1;
    best = Math.max(best, current);
    visit(node.left, node.val, current);
    visit(node.right, node.val, current);
  }
  if (root) visit(root, NaN, 0);
  return best;
}
