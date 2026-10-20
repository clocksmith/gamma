function invertTree(root) {
  if (root === null) {
    return null;
  }

  const stack = [root];

  while (stack.length > 0) {
    const node = stack.pop();
    [node.left, node.right] = [node.right, node.left];

    if (node.left !== null) {
      stack.push(node.left);
    }
    if (node.right !== null) {
      stack.push(node.right);
    }
  }

  return root;
}
