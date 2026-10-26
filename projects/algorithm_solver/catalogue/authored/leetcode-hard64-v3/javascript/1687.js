'use strict';

// 1687. Delivering Boxes from Storage to Ports: prefix weights, port changes and a monotonic DP deque; O(n) time and O(n) space.

function solve(boxes, portsCount, maxBoxes, maxWeight) {
  const size = boxes.length;
  const weight = Array(size + 1).fill(0);
  const changes = Array(size + 1).fill(0);
  for (let count = 1; count <= size; count += 1) {
    weight[count] = weight[count - 1] + boxes[count - 1][1];
    changes[count] = changes[count - 1] + (count > 1 && boxes[count - 1][0] !== boxes[count - 2][0] ? 1 : 0);
  }
  const best = Array(size + 1).fill(0);
  const queue = [0];
  let head = 0;
  for (let count = 1; count <= size; count += 1) {
    while (count - queue[head] > maxBoxes || weight[count] - weight[queue[head]] > maxWeight) head += 1;
    const previous = queue[head];
    best[count] = best[previous] + changes[count] - changes[previous + 1] + 2;
    if (count < size) {
      const value = best[count] - changes[count + 1];
      while (queue.length > head) {
        const last = queue[queue.length - 1];
        if (best[last] - changes[last + 1] < value) break;
        queue.pop();
      }
      queue.push(count);
    }
  }
  return best[size];
}

const boxDelivering = solve;
class Solution {
  boxDelivering(boxes, portsCount, maxBoxes, maxWeight) { return solve(boxes, portsCount, maxBoxes, maxWeight); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, boxDelivering };
