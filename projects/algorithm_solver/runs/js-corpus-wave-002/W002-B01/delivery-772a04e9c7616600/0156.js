function upsideDownBinaryTree(root) {
  let current = root;
  let previous = null;
  let previousRight = null;

  while (current !== null) {
    const next = current.left;
    current.left = previousRight;
    previousRight = current.right;
    current.right = previous;
    previous = current;
    current = next;
  }

  return previous;
}
