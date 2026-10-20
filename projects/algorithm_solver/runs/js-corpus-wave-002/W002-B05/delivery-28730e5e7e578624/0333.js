function largestBSTSubtree(root) {
  if (root === null) return 0;
  const information = new WeakMap();
  const stack = [[root, false]];
  const empty = { min: Infinity, max: -Infinity, size: 0 };
  let largest = 0;

  while (stack.length > 0) {
    const [node, ready] = stack.pop();
    if (!ready) {
      stack.push([node, true]);
      if (node.right !== null) stack.push([node.right, false]);
      if (node.left !== null) stack.push([node.left, false]);
      continue;
    }
    const left = node.left === null ? empty : information.get(node.left);
    const right = node.right === null ? empty : information.get(node.right);
    if (left.max < node.val && node.val < right.min) {
      const size = left.size + right.size + 1;
      largest = Math.max(largest, size);
      information.set(node, {
        min: Math.min(left.min, node.val),
        max: Math.max(right.max, node.val),
        size
      });
    } else {
      information.set(node, { min: -Infinity, max: Infinity, size: 0 });
    }
  }
  return largest;
}
