function verticalOrder(root) {
  if (root === null) return [];

  const columns = new Map();
  const queue = [[root, 0]];
  let firstColumn = 0;
  let lastColumn = 0;

  for (let index = 0; index < queue.length; index++) {
    const [node, column] = queue[index];
    if (!columns.has(column)) columns.set(column, []);
    columns.get(column).push(node.val);
    firstColumn = Math.min(firstColumn, column);
    lastColumn = Math.max(lastColumn, column);

    if (node.left !== null) queue.push([node.left, column - 1]);
    if (node.right !== null) queue.push([node.right, column + 1]);
  }

  const result = [];
  for (let column = firstColumn; column <= lastColumn; column++) {
    result.push(columns.get(column) || []);
  }
  return result;
}
