function countNodes(root) {
  function leftHeight(node) {
    let height = 0;
    let current = node;

    while (current !== null) {
      height += 1;
      current = current.left;
    }

    return height;
  }

  function rightHeight(node) {
    let height = 0;
    let current = node;

    while (current !== null) {
      height += 1;
      current = current.right;
    }

    return height;
  }

  if (root === null) {
    return 0;
  }

  const left = leftHeight(root);
  const right = rightHeight(root);

  if (left === right) {
    return (2 ** left) - 1;
  }

  return 1 + countNodes(root.left) + countNodes(root.right);
}
