function countConnectedComponents(adjacencyMatrix) {
  const nodeCount = adjacencyMatrix.length;
  const visitedNodes = new Array(nodeCount).fill(false);
  let componentCount = 0;
  for (let startIndex = 0; (startIndex < nodeCount); startIndex += 1) {
    if ((!visitedNodes[startIndex])) {
      componentCount += 1;
      visitedNodes[startIndex] = true;
      const pendingIndices = [startIndex];
      while (pendingIndices.length) {
        const nodeIndex = pendingIndices.pop();
        for (let neighborIndex = 0; (neighborIndex < nodeCount); neighborIndex += 1) {
          if ((adjacencyMatrix[nodeIndex][neighborIndex] && (!visitedNodes[neighborIndex]))) {
            visitedNodes[neighborIndex] = true;
            pendingIndices.push(neighborIndex);
          }
        }
      }
    }
  }
  return componentCount;
}
class Solution {
  findCircleNum(isConnected) {
    return countConnectedComponents(isConnected);
  }
}
