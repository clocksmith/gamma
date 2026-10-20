function findLeaves(root) {
  if (root === null) return [];
  const heights = new WeakMap();
  const stack = [[root, false]];
  const result = [];

  while (stack.length > 0) {
    const [node, visited] = stack.pop();
    if (!visited) {
      stack.push([node, true]);
      if (node.right !== null) stack.push([node.right, false]);
      if (node.left !== null) stack.push([node.left, false]);
      continue;
    }
    const leftHeight = node.left === null ? -1 : heights.get(node.left);
    const rightHeight = node.right === null ? -1 : heights.get(node.right);
    const height = Math.max(leftHeight, rightHeight) + 1;
    heights.set(node, height);
    if (!result[height]) result[height] = [];
    result[height].push(node.val);
  }
  return result;
}
