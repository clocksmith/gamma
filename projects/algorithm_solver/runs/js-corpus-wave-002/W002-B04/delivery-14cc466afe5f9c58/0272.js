function closestKValues(root, target, k) {
  const values = [];
  function visit(node) { if (!node) return; visit(node.left); values.push(node.val); visit(node.right); }
  visit(root);
  values.sort((a, b) => Math.abs(a - target) - Math.abs(b - target) || a - b);
  return values.slice(0, k);
}
