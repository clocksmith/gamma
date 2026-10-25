// External nodes have val, left and right; absent children are null.
function canonicalTree(root, intern) {
  if (root === null) {
    return 0;
  }
  const labels = new Map();
  const stack = [[root, false]];
  while (stack.length > 0) {
    const [node, expanded] = stack.pop();
    if (!expanded) {
      stack.push([node, true]);
      if (node.right !== null) {
        stack.push([node.right, false]);
      }
      if (node.left !== null) {
        stack.push([node.left, false]);
      }
    } else {
      const left = node.left === null ? 0 : labels.get(node.left);
      const right = node.right === null ? 0 : labels.get(node.right);
      const key = `${node.val},${Math.min(left, right)},${Math.max(left, right)}`;
      if (!intern.has(key)) {
        intern.set(key, intern.size + 1);
      }
      labels.set(node, intern.get(key));
    }
  }
  return labels.get(root);
}


class Solution {
  flipEquiv(root1, root2) {
    const intern = new Map();
    return canonicalTree(root1, intern) === canonicalTree(root2, intern);
  }
}
