function sumNumbers(root) {
  function visit(node, prefix) {
    if (node === null) {
      return 0;
    }

    const value = prefix * 10 + node.val;
    if (node.left === null && node.right === null) {
      return value;
    }

    return visit(node.left, value) + visit(node.right, value);
  }

  return visit(root, 0);
}
