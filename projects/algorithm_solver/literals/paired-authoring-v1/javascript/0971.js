class Solution {
  flipMatchVoyage(root, voyage) {
    const stack = root === null ? [] : [root];
    const flipped = [];
    let index = 0;
    while (stack.length > 0) {
      const node = stack.pop();
      if (index === voyage.length || node.val !== voyage[index]) return [-1];
      index += 1;
      const left = node.left;
      const right = node.right;
      if (left !== null && (index === voyage.length || left.val !== voyage[index])) {
        flipped.push(node.val);
        stack.push(left);
        if (right !== null) stack.push(right);
      } else {
        if (right !== null) stack.push(right);
        if (left !== null) stack.push(left);
      }
    }
    return index === voyage.length ? flipped : [-1];
  }
}
