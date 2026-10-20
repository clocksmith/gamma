function closestValue(root, target) {
  let closest = root.val, node = root;
  while (node) {
    const distance = Math.abs(node.val - target);
    const best = Math.abs(closest - target);
    if (distance < best || (distance === best && node.val < closest)) closest = node.val;
    node = target < node.val ? node.left : node.right;
  }
  return closest;
}
