function rightSideView(root) {
  if (root === null) {
    return [];
  }

  const result = [];
  const queue = [root];
  let start = 0;

  while (start < queue.length) {
    const levelEnd = queue.length;

    while (start < levelEnd) {
      const node = queue[start];
      start += 1;

      if (node.left !== null) {
        queue.push(node.left);
      }
      if (node.right !== null) {
        queue.push(node.right);
      }

      if (start === levelEnd) {
        result.push(node.val);
      }
    }
  }

  return result;
}
